"""Tiny synthetic fixtures. Production writers are exercised separately by C++ replay."""
import numpy as np
import uproot
from fixtures import chunk, raw_fixture
from analysis.raw.io import HITS_SCHEMA
from analysis.raw.preprocess import groups
from analysis.common.io import FORMAT_SCHEMA, TIMING_DEFINITION, PROCESSING_VERSION
from analysis.compact.io import SCHEMAS


def difficult_rows():
    rows=[]
    def add(event,track,particle,process='RadioactiveDecay',nucleus='A',**kw):
        rows.append(dict(EventNumber=event,ParticleID=track,ParentID=0,ParticleName=particle,
            ParticleTag={'e-':0,'e+':1,'gamma':2,'alpha':3}.get(particle,-1),
            ProcessType=process,Nucleus=nucleus,GlobalTime_ns=17.,**kw))
    add(0,1,'gamma');add(0,2,'nu_e')
    add(0,3,'alpha',EnergyDeposit=0,x_hits=40)
    add(0,3,'alpha',VolumeNumber=1)
    add(0,4,'e-',EnergyDeposit=.002)
    add(0,5,'e-','ionIoni','B')
    add(0,4,'e-',x_hits=7)  # Resumed track belongs to a second historical group.
    add(0,4,'e-',EnergyDeposit=0,x_hits=99)
    add(0,6,'e+','eIoni')
    add(0,7,'e-','phot','C',VolumeNumber=1)
    add(0,8,'e+','eIoni','D')
    add(1,1,'gamma')  # ignored first row must still flush the previous event
    add(1,2,'e-','eIoni')
    add(1,3,'e+','eIoni') # inherited initial ionization_seen=False updates label
    add(1,4,'e-','eIoni','B')
    add(2,1,'gamma') # event without groups
    add(3,1,'alpha') # EOF flush, alpha stays outside ER spectra
    return rows


def timed_chunk(records):
    return chunk(records) | {'GlobalTime_ns': np.array([r.get('GlobalTime_ns',17.) for r in records])}


def tables_from_groups(canonical,tracks):
    data={name:[] for name in SCHEMAS}
    for g in canonical:
        data['Groups'].append(dict(EventNumber=g.event,GroupIndex=g.group_index,ParticleName=g.particle,
            Nucleus=g.nucleus,ProcessType=g.process,StepCount=g.step_count,TrackCount=len(g.track_ids),VolumeCount=len(g.volumes)))
        for order,(number,v) in enumerate(g.volumes.items()):
            data['GroupVolumes'].append(dict(EventNumber=g.event,GroupIndex=g.group_index,VolumeOrder=order,
                VolumeNumber=number,EnergyDeposit=v.energy,x_first=v.x,y_first=v.y,z_first=v.z,FirstHitTime_ns=v.first_hit_time_ns))
    for t in tracks:
        data['Tracks'].append(dict(EventNumber=t.event,ParticleID=t.particle_id,ParticleTag=t.particle_tag,
            ParentID=t.parent_id,ParticleName=t.particle,Nucleus=t.nucleus,ProcessType=t.process,
            GroupIndex=-1 if not t.group_indices else t.group_indices[0] if len(t.group_indices)==1 else -2))
        data['TrackGroups'].extend(dict(EventNumber=t.event,ParticleID=t.particle_id,GroupIndex=g) for g in t.group_indices)
    return data


def fixture(path,expected,records=None,mode='both',requested=4,data=None):
    records=difficult_rows() if records is None else records
    tracks=[]
    canonical=list(groups([timed_chunk(records)],tracks.append))
    data=tables_from_groups(canonical,tracks) if data is None else data
    raw_fixture(path,expected,requested=requested)
    with uproot.update(path) as f:
        del f['Hits']
        if mode!='compact':
            f.mktree('Hits',HITS_SCHEMA)
            if records: f['Hits'].extend(timed_chunk(records))
        if mode!='raw':
            for name,schema in SCHEMAS.items():
                f.mktree(name,schema)
                if data[name]:
                    f[name].extend({k:np.array([r[k] for r in data[name]],dtype=object if kind=='string' else kind)
                                    for k,kind in schema.items()})
        f.mktree('OutputMetadata',FORMAT_SCHEMA)
        f['OutputMetadata'].extend(dict(OutputFormat=[mode],OutputSchemaVersion=np.array([1],dtype='int32'),
            TimingDefinition=[TIMING_DEFINITION],CompactProcessingVersion=[PROCESSING_VERSION]))
    return canonical,tracks,data
