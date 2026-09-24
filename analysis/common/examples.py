"""Small, explicitly SYNTHETIC notebook examples; never a physical rate estimate."""
from analysis.common.model import Group

IDENTITY=dict(layout='legacy-25x3',model='code-compatible',source_policy='historical',geometry_hash='synthetic')
GEOMETRY=dict(gas_size_mm=[100,120,140],gas_centers_mm={str(i):[0,0,0] for i in range(150)})


def canonical_groups():
    first=Group(0,'e-','synthetic nucleus','RadioactiveDecay')
    first.add(0,.012,0,0,0,17,2)
    first.add(1,.003,45,0,0,23,3)
    second=Group(1,'e+','synthetic nucleus','phot')
    second.add(0,.4,40,0,0,12,2)
    alpha=Group(2,'alpha','synthetic nucleus','RadioactiveDecay')
    alpha.add(0,.8,0,0,0,99,2)
    return [first,second,alpha]


def write_example(path):
    """Serialize a tiny both file using production preprocessing, for teaching IO."""
    import numpy as np
    import uproot
    from analysis.raw.io import HITS_SCHEMA
    from analysis.raw.preprocess import groups
    from analysis.compact.io import SCHEMAS
    from analysis.common.io import FORMAT_SCHEMA, TIMING_DEFINITION, PROCESSING_VERSION, METADATA
    from study.runtime import ACCOUNTING_FIELDS
    base=dict(EventNumber=0,ParticleName='e-',ParticleID=2,ParticleTag=0,ParentID=1,x_hits=0.,y_hits=0.,z_hits=0.,
        EnergyDeposit=0.,VolumeNumber=0,Nucleus='synthetic nucleus',ProcessType='RadioactiveDecay',GlobalTime_ns=17.)
    records=[base,base | dict(EnergyDeposit=.012,x_hits=99.,GlobalTime_ns=25.),
        base | dict(ParticleID=3,ProcessType='eIoni',VolumeNumber=1,EnergyDeposit=.003,GlobalTime_ns=23.),
        base | dict(EventNumber=1,ParticleName='gamma',ParticleTag=2,ParticleID=1,ParentID=0),
        base | dict(EventNumber=1,EnergyDeposit=.4,x_hits=40.,GlobalTime_ns=12.)]
    def arrays(rows,schema):
        return {key:np.array([row[key] for row in rows],dtype=object if kind=='string' else kind) for key,kind in schema.items()}
    chunks=arrays(records,HITS_SCHEMA);tracks=[];canonical=list(groups([chunks],tracks.append))
    data={name:[] for name in SCHEMAS}
    for g in canonical:
        data['Groups'].append(dict(EventNumber=g.event,GroupIndex=g.group_index,ParticleName=g.particle,
            Nucleus=g.nucleus,ProcessType=g.process,StepCount=g.step_count,TrackCount=len(g.track_ids),VolumeCount=len(g.volumes)))
        for order,(number,v) in enumerate(g.volumes.items()):
            data['GroupVolumes'].append(dict(EventNumber=g.event,GroupIndex=g.group_index,VolumeOrder=order,VolumeNumber=number,
                EnergyDeposit=v.energy,x_first=v.x,y_first=v.y,z_first=v.z,FirstHitTime_ns=v.first_hit_time_ns))
    for t in tracks:
        data['Tracks'].append(dict(EventNumber=t.event,ParticleID=t.particle_id,ParticleTag=t.particle_tag,ParentID=t.parent_id,
            ParticleName=t.particle,Nucleus=t.nucleus,ProcessType=t.process,
            GroupIndex=-1 if not t.group_indices else t.group_indices[0] if len(t.group_indices)==1 else -2))
        data['TrackGroups'].extend(dict(EventNumber=t.event,ParticleID=t.particle_id,GroupIndex=g) for g in t.group_indices)
    with uproot.recreate(path) as f:
        f.mktree('Hits',HITS_SCHEMA);f['Hits'].extend(chunks)
        for name,schema in SCHEMAS.items():
            f.mktree(name,schema)
            if data[name]: f[name].extend(arrays(data[name],schema))
        f.mktree('RunMetadata',dict.fromkeys(METADATA,'string'))
        f['RunMetadata'].extend({k:[IDENTITY[v]] for k,v in METADATA.items()})
        f.mktree('RunAccounting',dict.fromkeys(ACCOUNTING_FIELDS,'int32'))
        f['RunAccounting'].extend({k:np.array([0 if k in ('RunID','AbortedEvents') else 2],dtype='int32') for k in ACCOUNTING_FIELDS})
        f.mktree('OutputMetadata',FORMAT_SCHEMA)
        f['OutputMetadata'].extend(dict(OutputFormat=['both'],OutputSchemaVersion=np.array([1],dtype='int32'),
            TimingDefinition=[TIMING_DEFINITION],CompactProcessingVersion=[PROCESSING_VERSION]))
