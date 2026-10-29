"""Independent event accounting, recoil retention and external/internal separation."""
import copy
import csv
import json
import math
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import numpy as np
import uproot
from study import runtime as rt
from external.study.config import load,validate,macro,rate,PROCESSING,PHYSICS
from external.study.simulate import check_campaign,run
from external.analysis.raw.preprocess import groups as raw_groups
from external.analysis.io import groups, SIMULATION_SCHEMA
from external.analysis.analyze import spectra,analyze,CHANNELS
from analysis.common.io import FORMAT_SCHEMA,TIMING_DEFINITION,output_metadata
from analysis.common.model import TrackRecord
from analysis.compact.preprocess import reconstruct
from compact_fixtures import timed_chunk,tables_from_groups,SCHEMAS
from fixtures import raw_fixture,environment,log_for

CONFIG=rt.REPO/'external/config/hall-c-gamma-2026-proxy.json'


def records():
    return [dict(EventNumber=e,ParticleID=t,ParticleName=p,ParentID=0,ParticleTag={'e-':0,'gamma':2,'alpha':3}.get(p,-1),
                 EnergyDeposit=d,ProcessType='hadElastic' if p=='F19' else '',Nucleus='',GlobalTime_ns=1.,VolumeNumber=v)
            for e,t,p,d,v in [(0,1,'neutron',0,0),(0,2,'F19',.004,0),(0,3,'e-',.006,0),
                              (0,2,'F19',.001,1),(1,1,'gamma',0,0),(2,1,'proton',.4,0),(3,1,'e-',1.,0)]]


def fixture(folder,mode='both',layout='cygno-11x7-v1',model='cygno-acrylic-v3'):
    folder.mkdir();attempt=folder/'attempt-0002';attempt.mkdir()
    cfg=load(CONFIG)|dict(primaries=5,output_mode=mode,layout=layout)
    if model is None:cfg.pop('model') # original pre-model v2 campaign
    else:cfg['model']=model
    actual_model=cfg.get('model','cygno-300elj-v2')
    env=environment()|dict(physics=PHYSICS+'+G4RadioactiveDecayPhysics')
    identity=dict(config=cfg,environment=env,source_radius_mm=1000.,external_geometry_hash='fixture-shield',source={'files_sha256':{}})
    c=dict(external_campaign_version=1,status='complete',identity=identity,fingerprint=rt.object_digest(identity),
           attempt=attempt.name,data_path='outfiles_V2/'+mode+'.root',incident_rate_s=rate(cfg,1000.),
           accounting=dict(RunID=0,RequestedEvents=5,GeneratedPrimaries=5,ProcessedEvents=5,AbortedEvents=0))
    expected=dict(geometry_hash=env['geometry_hash'],layout=cfg['layout'],model=actual_model,source_policy='environmental-surface-v1')
    data=attempt/c['data_path'];raw_fixture(data,expected,requested=5)
    rows=records();chunk=timed_chunk(rows);canonical=list(raw_groups([chunk]))
    tracks=[]
    for g in canonical:
        row=next(r for r in rows if r['EventNumber']==g.event and r['ParticleID'] in g.track_ids)
        tracks.append(TrackRecord(g.event,row['ParticleID'],row['ParticleTag'],row['ParentID'],
                                  row['ParticleName'],row['Nucleus'],row['ProcessType'],[g.group_index]))
    tracks.sort(key=lambda t:(t.event,t.particle_id))
    tables=tables_from_groups(canonical,tracks)
    with uproot.update(data) as f:
        del f['Hits']
        if mode!='compact':
            from analysis.raw.io import HITS_SCHEMA
            f.mktree('Hits',HITS_SCHEMA);f['Hits'].extend(chunk)
        if mode!='raw':
            for name,schema in SCHEMAS.items():
                f.mktree(name,schema)
                if tables[name]:f[name].extend({k:np.array([r[k] for r in tables[name]],dtype=object if typ=='string' else typ) for k,typ in schema.items()})
        f.mktree('OutputMetadata',FORMAT_SCHEMA)
        f['OutputMetadata'].extend(dict(OutputFormat=[mode],OutputSchemaVersion=np.array([1],dtype='int32'),TimingDefinition=[TIMING_DEFINITION],CompactProcessingVersion=[PROCESSING]))
        f.mktree('SimulationMetadata',SIMULATION_SCHEMA)
        f['SimulationMetadata'].extend({k:np.array([v],dtype='float64') if k=='SourceRadius_mm' else [v] for k,v in dict(Mode='external',Shielding=cfg['shield'],PhysicsList=PHYSICS,SourceHash=env['source_hash'],ExternalGeometryHash=identity['external_geometry_hash'],SourceRadius_mm=1000.).items()})
    rt.save(folder/'config.json',cfg)
    rt.save(folder/'geometry.json',dict(layout=cfg['layout'],model=actual_model,geometry_hash=env['geometry_hash'],source_hash=env['source_hash'],gas_centers_mm={str(i):[0,0,0] for i in range(154 if layout=='cygno-11x7-v1' else 150)}))
    c['geometry_sha256']=rt.digest(folder/'geometry.json')
    (attempt/'run.mac').write_text(macro(cfg))
    (attempt/'simulation.log').write_text(log_for(env,5)+f"CYGNO layout={cfg['layout']} detector_model={actual_model} source_model=environmental-surface-v1\nCYGNO_EXTERNAL radius_mm 1000\nCYGNO_EXTERNAL geometry_hash fixture-shield\n")
    rt.save(attempt/'simulation.command.json',dict(returncode=0,command=['rdecay01','--model',actual_model]))
    c['artifacts']=rt.artifacts(attempt)
    rt.save(attempt/'manifest.json',c);rt.save(folder/'campaign.json',c)
    return c,data,canonical,tables


class ExternalTests(unittest.TestCase):
    def test_models_and_archived_v2_are_checked_without_relabeling(self):
        with tempfile.TemporaryDirectory() as tmp:
            for model in (None,'cygno-300elj-v2','cygno-acrylic-v3','cygno-copper-cathode-v4'):
                root=Path(tmp)/str(model)
                campaign,data,canonical,_=fixture(root,model=model)
                before={p.relative_to(root):rt.digest(p) for p in root.rglob('*') if p.is_file()}
                check_campaign(root)
                with uproot.open(data) as file:
                    self.assertEqual(list(groups(file,campaign)),canonical)
                    wrong=copy.deepcopy(campaign)
                    wrong['identity']['config']['model']='cygno-300elj-v2' if model=='cygno-acrylic-v3' else 'cygno-acrylic-v3'
                    with self.assertRaisesRegex(ValueError,'identity'):list(groups(file,wrong))
                self.assertEqual(before,{p.relative_to(root):rt.digest(p) for p in root.rglob('*') if p.is_file()})

    def test_config_and_flux_conventions(self):
        cfg=load(CONFIG)
        self.assertEqual(cfg['model'],'cygno-copper-cathode-v4')
        missing=cfg.copy();missing.pop('model')
        with self.assertRaises(ValueError):validate(missing)
        self.assertEqual(validate(missing,historical=True),missing)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'original-config.json';rt.save(path,missing)
            with self.assertRaises(ValueError):load(path)
            self.assertEqual(load(path,model='cygno-300elj-v2')['model'],'cygno-300elj-v2')
            self.assertEqual(rt.read(path),missing)
        self.assertAlmostEqual(rate(cfg,10),.46*4*math.pi)
        self.assertAlmostEqual(rate(cfg|dict(flux_convention='scalar'),10),.46*math.pi)
        self.assertIn('/gps/hist/point 0.057000000000000002 0',macro(cfg))
        self.assertNotIn('RadElement',macro(cfg))
        n=load(rt.REPO/'external/config/hall-c-neutron-wulandari-proxy.json')
        self.assertAlmostEqual(sum(n['bin_probabilities']),1)
        for cfg,name in [(cfg,'gamma.mac'),(n,'neutron.mac')]:
            self.assertEqual((rt.REPO/'external/macros'/name).read_text().split('\n',1)[1],macro(cfg))
        cfg=load(CONFIG)
        for key,value in [('model','unknown'),('primaries',0),('id','../bad'),('scientific_status','proxy\n/run/beamOn 1'),('flux_cm2_s',float('nan')),('flux_convention','unknown'),('energy_edges_MeV',[2,1]),('bin_probabilities',[1,1])]:
            with self.subTest(key=key),self.assertRaises(ValueError):validate(cfg|{key:value})

    def test_raw_compact_parity_and_empty_primary_denominator(self):
        expected=None
        with tempfile.TemporaryDirectory() as tmp:
            for mode in ('raw','compact','both'):
                root=Path(tmp)/mode;c,path,canonical,tables=fixture(root,mode)
                with uproot.open(path) as f:
                    self.assertEqual(list(groups(f,c,1)),canonical)
                    with self.assertRaises(ValueError):output_metadata(f)
                report=analyze(root,Path(tmp)/('analysis-'+mode))
                values=(report['counts'],report['windows'],report['scale_per_year'])
                if expected is None:expected=values
                self.assertEqual(values,expected)
                self.assertEqual(report['generated_primaries'],5) # includes empty event 4 and zero-only event 1
                self.assertEqual(report['windows']['total'],dict(positive=3,gt10_le400=2))
                self.assertEqual(report['windows']['charged_hadron'],dict(positive=2,gt10_le400=1))
                self.assertEqual(report['counts']['total'][1001],1)
                # Repeating a completed check is read-only; altered bytes fail the integrity gate.
                check_campaign(root)
                with path.open('ab') as f:f.write(b'changed')
                with self.assertRaises(ValueError):check_campaign(root)

    def test_recoil_relationships_are_external_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            c,path,canonical,tables=fixture(Path(tmp)/'campaign')
            data={name:[r for r in rows if r['EventNumber']==0] for name,rows in tables.items()}
            self.assertEqual(reconstruct(0,data,c['identity']['config']['layout'],external=True)[0],canonical[:3])
            with self.assertRaises(ValueError):reconstruct(0,data,c['identity']['config']['layout'])
            malformed=copy.deepcopy(data);malformed['Tracks'][1]['ParticleName']='C12'
            with self.assertRaises(ValueError):reconstruct(0,malformed,c['identity']['config']['layout'],external=True)
            malformed=copy.deepcopy(data);malformed['TrackGroups'].pop()
            with self.assertRaises(ValueError):reconstruct(0,malformed,c['identity']['config']['layout'],external=True)

    def test_runner_failure_retry_and_reuse_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build=root/'build';build.mkdir()
            for name in ('rdecay01','geometry_quantities'):(build/name).write_bytes(b'fixture')
            cfg=load(CONFIG)|dict(primaries=5);config=root/'config.json';rt.save(config,cfg)
            args=SimpleNamespace(config=config,build=build,output=root/'campaign',primaries=None,seed=None,
                                 shield=None,output_mode=None,model=None,dry_run=False,retry_failed=False)
            env=environment()|dict(physics=PHYSICS+'+G4RadioactiveDecayPhysics',source_hash='fixture')
            shield_hash=rt.digest(rt.REPO/'common/ExternalGeometry.hh')
            text=log_for(env,5)+f"CYGNO layout={cfg['layout']} detector_model={cfg['model']} source_model=environmental-surface-v1\n"+f'CYGNO_EXTERNAL radius_mm 1000\nCYGNO_EXTERNAL geometry_hash {shield_hash}\n'
            calls=[]
            def invoke(command,cwd,label,timeout,**kwargs):
                rt.save(cwd/(label+'.command.json'),dict(returncode=0,command=list(map(str,command))))
                transport_text=text.replace('detector_model='+cfg['model'],'detector_model='+(args.model or cfg['model']))
                (cwd/(label+'.log')).write_text(transport_text)
                if label=='geometry':
                    Path(command[1]).write_text('diagnostic quantities')
                    self.assertEqual(command[-2:],['--model',args.model or cfg['model']])
                    rt.save(Path(command[3]),dict(source_hash='fixture',model=cfg['model'],layout=cfg['layout'],geometry_hash=env['geometry_hash'],source_policy='environmental-surface-v1'))
                if label=='simulation':
                    calls.append(cwd)
                    folder=cwd/'outfiles_V2';folder.mkdir();(folder/'compact.root').write_bytes(b'fixture')
                    if len(calls)==1:raise ValueError('synthetic transport failure')
                self.assertEqual(command[-2:],['--model',args.model or cfg['model']])
                return transport_text
            with patch.object(rt,'invoke',side_effect=invoke),patch.object(rt,'source_state',return_value={'files_sha256':{}}), \
                 patch.object(rt,'dataset_state',return_value={}),patch.object(rt,'compiled_source_hash',return_value='fixture'):
                with self.assertRaises(ValueError):run(args)
                self.assertEqual(rt.read(args.output/'campaign.json')['status'],'failed')
                with self.assertRaises(ValueError):run(args)
                args.retry_failed=True;self.assertEqual(run(args),0)
                self.assertEqual(rt.read(args.output/'campaign.json')['attempt'],'attempt-0002')
                self.assertNotIn('error',rt.read(args.output/'campaign.json'))
                self.assertEqual(rt.read(args.output/'attempt-0001/manifest.json')['status'],'failed')
                self.assertTrue((args.output/'attempt-0001/outfiles_V2/compact.root').is_file())
                self.assertEqual(run(args),0);self.assertEqual(len(calls),2)
                args.model='cygno-300elj-v2'
                with self.assertRaises(ValueError):run(args)
                args.model=None
                args.primaries=6
                with self.assertRaises(ValueError):run(args)

    def test_production_accumulator_retains_resumed_recoils(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/'accumulate'
            subprocess.run(['c++','-std=c++17','-I'+str(rt.REPO/'include'),str(rt.REPO/'validation/compact_accumulator.cc'),'-o',str(exe)],check=True,capture_output=True)
            rows=records()
            payload='\n'.join(f'{r["EventNumber"]} {r["ParticleID"]} {r["ParticleTag"]} {r["ParentID"]} {r["VolumeNumber"]} "{r["ParticleName"]}" "" "{r["ProcessType"]}" 0 0 0 {r["EnergyDeposit"]} 1' for r in rows)+'\n'
            result=subprocess.check_output([str(exe),'--external'],input=payload,text=True)
            emitted=[shlex.split(line) for line in result.splitlines()]
            self.assertEqual(sum(r[0]=='G' for r in emitted),6)
            fluorine=next(r for r in emitted if r[0]=='G' and r[3]=='F19')
            self.assertEqual(fluorine[-3:],['2','1','2'])
            self.assertEqual(sum(float(r[5]) for r in emitted if r[0]=='V'),sum(r['EnergyDeposit'] for r in rows))


@unittest.skipUnless(shutil.which('root-config'),'ROOT is not installed')
class ExternalRootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.exe=Path(cls.tmp.name)/'AnalyzeExternal'
        flags=shlex.split(subprocess.check_output(['root-config','--cflags','--libs'],text=True))
        command=['c++','-O2','-std=c++17','-ffp-contract=off',str(rt.REPO/'external/analysis/common_c++/AnalyzeExternal.cpp'),*flags,'-lRooFitHS3']
        libdir=Path(subprocess.check_output(['root-config','--libdir'],text=True).strip())
        if any(libdir.glob('libRooFitJSONInterface.*')):command+=['-lRooFitJSONInterface']
        subprocess.run([*command,'-o',str(cls.exe)],check=True,capture_output=True)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_native_root_matches_python_and_rejects_mixed_identity(self):
        for layout,mode,model in [('legacy-25x3','compact',None),('cygno-11x7-v1','both','cygno-acrylic-v3'),('cygno-5x5x3-v1','compact','cygno-300elj-v2')]:
            with self.subTest(layout=layout),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);c,data,_,_=fixture(root/'campaign',mode,layout,model)
                python=analyze(root/'campaign',root/'python')
                result=subprocess.run([str(self.exe),str(root/'campaign'),str(root/'cpp')],capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                with (root/'cpp/spectra.tsv').open() as f:
                    for row in csv.DictReader(f,delimiter='\t'):
                        n=python['counts'][row['channel']][int(row['bin'])]
                        self.assertEqual(int(row['MC_events']),n)
                        self.assertAlmostEqual(float(row['annual_events']),n*python['scale_per_year'],delta=max(1e-12,abs(n*python['scale_per_year'])*1e-14))
                for name in ('spectra.png','spectra.pdf','analysis.root','summary.txt'):
                    self.assertGreater((root/'cpp'/name).stat().st_size,0)
                c['identity']['config']['shield']='none';rt.save(root/'campaign/campaign.json',c)
                result=subprocess.run([str(self.exe),str(root/'campaign'),str(root/'invalid')],capture_output=True)
                self.assertNotEqual(result.returncode,0)
                self.assertFalse((root/'invalid').exists())
