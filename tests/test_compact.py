import copy
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import uproot
from study import runtime as rt, simulate
from study.analyze import analyze, analysis_source_state
from study.archive import package, open_campaign
from study.campaign import validate_campaign
from study.source_matrix import read_matrix
from analysis.raw.io import header as raw_header, hit_chunks
from analysis.raw.preprocess import groups as raw_groups
from analysis.compact.io import header as compact_header, SCHEMAS
from analysis.compact.preprocess import groups as compact_groups
from analysis.compact.parity import validate
from analysis.common.io import output_metadata
from analysis.common.spectra import accumulate, summarize, scale_for
from analysis.common.reporting import write_tables
from fixtures import raw_fixture, campaign_fixture, environment, log_for
from compact_fixtures import fixture, difficult_rows, timed_chunk, tables_from_groups

EXPECTED=dict(layout='legacy-25x3',model='code-compatible',source_policy='historical',geometry_hash='fixture')
GEOMETRY=dict(gas_size_mm=[100]*3,gas_centers_mm={str(i):[0]*3 for i in range(150)})

class CompactTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'both.root'

    def read(self):
        with uproot.open(self.path) as f:
            _,trees=compact_header(f,EXPECTED,4)
            tracks=[]
            result=list(compact_groups(trees,4,EXPECTED['layout'],1,tracks.append))
            return result,tracks

    def test_reconstruction_timing_boundaries_and_tracks(self):
        canonical,tracks,_=fixture(self.path,EXPECTED)
        self.assertEqual(self.read(),(canonical,tracks))
        self.assertEqual(len(canonical),5)
        self.assertEqual(canonical[0].volumes[0].x,40)
        self.assertEqual(canonical[0].volumes[0].first_hit_time_ns,17)
        self.assertEqual(list(canonical[0].volumes),[0,1])
        self.assertEqual(canonical[3].particle,'e+')
        self.assertEqual(next(t for t in tracks if t.event==0 and t.particle_id==4).group_indices,[0,1])
        records=difficult_rows()
        for split in range(len(records)+1):
            self.assertEqual(list(raw_groups([timed_chunk(records[:split]),timed_chunk(records[split:])])),canonical)
        with uproot.open(self.path) as f:
            self.assertEqual(validate(f,EXPECTED,4,GEOMETRY,1)['status'],'passed')
        # Time comes from first encounter, not minimum time or first positive deposit.
        records[2]['GlobalTime_ns']=99.;records[4]['GlobalTime_ns']=1.
        g=list(raw_groups([timed_chunk(records)]))[0]
        self.assertEqual(g.volumes[0].first_hit_time_ns,99.)
        self.assertEqual(g.volumes[0].x,40.)

    def test_legacy_and_new_raw_contract(self):
        raw_fixture(self.path,EXPECTED,[{}],requested=4)
        with uproot.open(self.path) as f:
            _,hits=raw_header(f,EXPECTED,4)
            self.assertIsNone(next(raw_groups(hit_chunks(hits,4,EXPECTED['layout']))).volumes[0].first_hit_time_ns)
            self.assertEqual(output_metadata(f)['OutputSchemaVersion'],0)
        fixture(self.path,EXPECTED,mode='raw')
        with uproot.open(self.path) as f:
            raw_header(f,EXPECTED,4)
            with self.assertRaises(ValueError): output_metadata(f,'compact',1)
        with uproot.update(self.path) as f: del f['OutputMetadata']
        with uproot.open(self.path) as f, self.assertRaises(ValueError): raw_header(f,EXPECTED,4)
        fixture(self.path,EXPECTED,mode='compact')
        with uproot.open(self.path) as f:
            self.assertNotIn('Hits',f)
            with self.assertRaises(ValueError): raw_header(f,EXPECTED,4)
        with uproot.update(self.path) as f: del f['OutputMetadata']
        with uproot.open(self.path) as f, self.assertRaises(ValueError): compact_header(f,EXPECTED,4)

    def test_malformed_relationships(self):
        _,_,original=fixture(self.path,EXPECTED)
        mutations=[
            lambda d:d['Groups'].append(d['Groups'][-1].copy()),
            lambda d:d['Groups'][0].update(GroupIndex=1),
            lambda d:d['Groups'][0].update(StepCount=0),
            lambda d:d['Groups'][0].update(TrackCount=99),
            lambda d:d['Groups'][0].update(VolumeCount=99),
            lambda d:d['Groups'][0].update(ParticleName='gamma'),
            lambda d:d['GroupVolumes'][0].update(VolumeOrder=1),
            lambda d:d['GroupVolumes'][1].update(VolumeNumber=0),
            lambda d:d['GroupVolumes'][0].update(GroupIndex=99),
            lambda d:d['GroupVolumes'][0].update(FirstHitTime_ns=float('nan')),
            lambda d:d['GroupVolumes'][0].update(VolumeNumber=150),
            lambda d:d['Tracks'][0].update(ParticleID=0),
            lambda d:d['Tracks'][1].update(ParticleID=1),
            lambda d:d['Tracks'][0].update(ParentID=1),
            lambda d:d['Tracks'][0].update(ParticleTag=9),
            lambda d:d['Tracks'][0].update(GroupIndex=0),
            lambda d:d['TrackGroups'][0].update(ParticleID=99),
            lambda d:d['TrackGroups'][0].update(GroupIndex=99),
            lambda d:d['TrackGroups'].insert(1,d['TrackGroups'][0].copy()),
            lambda d:d['TrackGroups'].pop(),
            lambda d:d['Tracks'][0].update(EventNumber=-1),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutations.index(mutate)):
                data=copy.deepcopy(original);mutate(data);fixture(self.path,EXPECTED,data=data)
                with self.assertRaises(ValueError): self.read()
        fixture(self.path,EXPECTED)
        with uproot.update(self.path) as f: del f['Tracks']
        with self.assertRaises(ValueError): self.read()

    def test_timing_inactive_all_rates_categories_tables(self):
        canonical,_,_=fixture(self.path,EXPECTED)
        compact,_=self.read()
        altered=copy.deepcopy(canonical)
        for group in altered:
            for volume in group.volumes.values(): volume.first_hit_time_ns=1e100
        results=[accumulate(stream,GEOMETRY) for stream in (canonical,compact,altered)]
        for result in results[1:]:
            for a,b in zip(results[0],result): np.testing.assert_array_equal(a,b)
        matrix=read_matrix(rt.REPO/'config/study/thesis-table7.1.json')
        quantities={r['component']:dict(mass_kg=2.,pieces=750) for r in matrix['contributions']}
        spectra=[]
        for c,h,_ in results:
            spectra.append(summarize([(r,scale_for(r,quantities,4),c,h) for r in matrix['contributions']]))
        self.assertEqual(spectra[0],spectra[1]);self.assertEqual(spectra[0],spectra[2])
        for i,s in enumerate(spectra):
            folder=Path(self.tmp.name)/str(i);folder.mkdir()
            write_tables(folder,s,dict(mode='smoke',coverage='26/26',complete_matrix=True))
        for name in ('tables.json','table7.2.csv','table7.3.csv'):
            self.assertEqual((Path(self.tmp.name)/'0'/name).read_bytes(),(Path(self.tmp.name)/'1'/name).read_bytes())
        # Parity rejects a timing change even though the scientific spectrum is identical.
        _,_,data=fixture(self.path,EXPECTED)
        data['GroupVolumes'][0]['FirstHitTime_ns']+=1
        fixture(self.path,EXPECTED,data=data)
        with uproot.open(self.path) as f, self.assertRaises(ValueError): validate(f,EXPECTED,4,GEOMETRY)

    def test_compact_types_and_metadata(self):
        from analysis.common.io import FORMAT_SCHEMA, TIMING_DEFINITION, PROCESSING_VERSION
        for name,field in [('Groups','StepCount'),('GroupVolumes','FirstHitTime_ns'),('Tracks','ParticleID')]:
            fixture(self.path,EXPECTED)
            with uproot.update(self.path) as f:
                del f[name]
                schema=SCHEMAS[name] | {field:'float32'}
                f.mktree(name,schema)
            with self.assertRaises(ValueError): self.read()
        for change in [dict(OutputSchemaVersion=2),dict(OutputFormat='unknown'),
                       dict(TimingDefinition='absolute'),dict(CompactProcessingVersion='new')]:
            fixture(self.path,EXPECTED)
            with uproot.update(self.path) as f:
                del f['OutputMetadata']
                f.mktree('OutputMetadata',FORMAT_SCHEMA)
                values=dict(OutputFormat='both',OutputSchemaVersion=1,TimingDefinition=TIMING_DEFINITION,
                            CompactProcessingVersion=PROCESSING_VERSION) | change
                f['OutputMetadata'].extend({k:np.array([v],dtype='int32') if k=='OutputSchemaVersion' else [v]
                                            for k,v in values.items()})
            with self.assertRaises(ValueError): self.read()

    def test_empty_and_ignored_only_events(self):
        for records in ([],[dict(EventNumber=0,ParticleName='gamma',ParticleTag=2)]):
            canonical,tracks,_=fixture(self.path,EXPECTED,records=records)
            self.assertEqual(self.read(),(canonical,tracks))
            with uproot.open(self.path) as f: self.assertEqual(validate(f,EXPECTED,4,GEOMETRY)['groups'],0)

    @unittest.skipUnless(shutil.which('c++'),'C++17 compiler required for accumulator replay')
    def test_cpp_state_machine_event_end_and_inferred_boundary(self):
        binary=Path(self.tmp.name)/'replay'
        subprocess.run(['c++','-std=c++17','-I'+str(rt.REPO/'include'),str(rt.REPO/'validation/compact_accumulator.cc'),'-o',str(binary)],check=True)
        # Includes resumed track, nonzero time, zero steps, ignored rows, merged tracks and EOF.
        records=difficult_rows();chunk=timed_chunk(records)
        order=('EventNumber','ParticleID','ParticleTag','ParentID','VolumeNumber','ParticleName','Nucleus','ProcessType',
               'x_hits','y_hits','z_hits','EnergyDeposit','GlobalTime_ns')
        lines=[' '.join(json.dumps(chunk[k][i].item() if hasattr(chunk[k][i],'item') else chunk[k][i]) for k in order)
               for i in range(len(records))]
        outputs=[]
        for explicit in (False,True):
            outputs.append(subprocess.check_output([binary,*(['event-end'] if explicit else [])],input='\n'.join(lines),text=True))
        self.assertEqual(*outputs)
        data={name:[] for name in SCHEMAS}
        for line in outputs[0].splitlines():
            kind,*values=shlex.split(line);name=dict(G='Groups',V='GroupVolumes',T='Tracks',L='TrackGroups')[kind]
            data[name].append({k: str(v) if t=='string' else int(v) if t=='int32' else float(v)
                              for (k,t),v in zip(SCHEMAS[name].items(),values)})
        canonical,tracks,_=fixture(self.path,EXPECTED,data=data)
        self.assertEqual(self.read(),(canonical,tracks))
        with uproot.open(self.path) as f: validate(f,EXPECTED,4,GEOMETRY,1)

class NewCampaignTests(unittest.TestCase):
    def test_each_mode_archive_analysis_and_legacy(self):
        with tempfile.TemporaryDirectory() as directory:
            spectra=[]
            for mode in ('raw','compact','both'):
                root=Path(directory)/mode
                config,matrix,campaign=campaign_fixture(root)
                config.update(output_mode=mode,output_schema_version=1)
                rt.save(root/'config.json',config)
                campaign.update(schema_version=3,fingerprint=rt.object_digest(campaign['identity']))
                campaign['snapshots']['config.json']=rt.digest(root/'config.json')
                rt.save(root/'campaign.json',campaign)
                def invoke(command,cwd,label,timeout,**options):
                    expected=EXPECTED | dict(geometry_hash=environment()['geometry_hash'])
                    fixture(cwd/'outfiles_V2'/f'{mode}.root',expected,
                            records=[dict(EnergyDeposit=.02),dict(EventNumber=1,EnergyDeposit=.4)],mode=mode,requested=2)
                    log=log_for(environment(),2);(cwd/(label+'.log')).write_text(log)
                    rt.save(cwd/(label+'.command.json'),dict(command=list(map(str,command)),returncode=0));return log
                with patch.object(rt,'invoke',side_effect=invoke):
                    for row in matrix['contributions']: simulate.run_job(root,row,config,campaign,'fixture')
                simulate.update_campaign(root,campaign,matrix)
                self.assertEqual(len(validate_campaign(root)),26)
                archive=package(root)
                with open_campaign(archive) as extracted:
                    out=Path(directory)/(mode+'-analysis')
                    self.assertEqual(analyze(extracted,out),0)
                    manifest=rt.read(out/'analysis-manifest.json')
                    self.assertEqual(manifest['inputs'][matrix['contributions'][0]['id']]['output_format']['OutputFormat'],mode)
                    if mode=='both':
                        self.assertEqual(manifest['inputs'][matrix['contributions'][0]['id']]['parity']['status'],'passed')
                        self.assertEqual(manifest['normalized_parity']['status'],'passed')
                    spectra.append(rt.read(out/'spectra.json'))
            self.assertEqual(spectra[0],spectra[1]);self.assertEqual(spectra[0],spectra[2])

    def test_archived_provenance_covers_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            names=['study/analyze.py','study/requirements-analysis.txt',
                   'analysis/raw/preprocess.py','analysis/compact/preprocess.py','analysis/common/spectra.py']
            for name in names:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture')
            with patch.object(rt,'REPO',root): state=analysis_source_state()
            self.assertEqual(set(state['files_sha256']),set(names))

@unittest.skipUnless(os.environ.get('CYGNO_TRANSPORT_BUILD'),'Set CYGNO_TRANSPORT_BUILD for 30-primary Geant4 integration')
class TransportTests(unittest.TestCase):
    def test_same_transport(self):
        from validation.compact_transport import run
        with tempfile.TemporaryDirectory() as directory:
            result=run(Path(os.environ['CYGNO_TRANSPORT_BUILD']).resolve(),Path(directory)/'run')
            self.assertTrue(result['transport_unchanged'])
