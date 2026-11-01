"""Synthetic software validation only: no transport or CNAF worker compatibility evidence."""
import copy
import csv
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import uproot
import test_external
from external.merge import merge as join
from external.study.config import macro
from external.study.simulate import check_campaign
from external.analysis.analyze import spectra
from study import runtime as rt
from fixtures import environment


def completed(path, seed=730000001, primaries=1000000000):
    env = environment() | dict(source_hash=rt.compiled_source_hash())
    with patch.object(test_external, 'environment', return_value=env):
        c, data, canonical, _ = test_external.fixture(path, mode='compact', model='cygno-copper-cathode-v4')
    c['identity']['config'].update(seed=seed, primaries=primaries)
    c['identity']['executable_sha256'] = rt.object_digest('synthetic-executable')
    files = join.build_files({str(p.relative_to(rt.REPO)):rt.digest(p) for p in rt.REPO.rglob('*') if p.is_file() and '.git' not in p.parts})
    c['identity']['source'] = dict(revision='synthetic', files_sha256=files)
    c['identity']['datasets'] = {k:dict(path='/synthetic/'+k, version_directory=k, files=1,
                                         content_sha256=rt.object_digest(k)) for k in rt.ENV_KEYS}
    for name in files:
        target = path/'source'/name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(rt.REPO/name, target)
    a = c['accounting']; a.update(RequestedEvents=primaries, GeneratedPrimaries=primaries, ProcessedEvents=primaries)
    with uproot.update(data) as f:
        del f['RunAccounting']; f.mktree('RunAccounting', {k:'int32' for k in a})
        f['RunAccounting'].extend({k:np.array([v],dtype='int32') for k,v in a.items()})
    attempt = data.parent.parent
    log = (attempt/'simulation.log').read_text()
    log = '\n'.join('CYGNO_ACCOUNTING '+json.dumps(a) if line.startswith('CYGNO_ACCOUNTING ') else line for line in log.splitlines())+'\n'
    (attempt/'simulation.log').write_text(log)
    (attempt/'run.mac').write_text(macro(c['identity']['config']))
    save(path,c)
    return c,data,canonical


def save(path, c):
    c['fingerprint'] = rt.object_digest(c['identity'])
    rt.save(path/'config.json', c['identity']['config'])
    c['artifacts'] = rt.artifacts(path/c['attempt'])
    rt.save(path/c['attempt']/'manifest.json', c); rt.save(path/'campaign.json', c)


class MergeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name); self.a=self.base/'a'; self.b=self.base/'b'
        self.ca,self.da,self.canonical=completed(self.a)
        self.cb,self.db,_=completed(self.b,seed=730000002,primaries=1500000000)

    def test_logical_join_read_only_large_total_and_tampering(self):
        before = {str(p):rt.digest(p) for d in (self.a,self.b) for p in d.rglob('*') if p.is_file()}
        out=self.base/'joined'; c=join.merge(out,[self.a,self.b])
        self.assertEqual(c['generated_primaries'],2500000000)
        self.assertEqual(join.verify(out,full=True),c)
        self.assertEqual(list(out.iterdir()),[out/'campaign.json'])
        self.assertEqual(before,{str(p):rt.digest(p) for d in (self.a,self.b) for p in d.rglob('*') if p.is_file()})
        with self.assertRaises(ValueError): join.merge(out,[self.a,self.b])
        with self.db.open('ab') as f:f.write(b'tampered')
        with self.assertRaises(ValueError): join.verify(out)

    def test_duplicates_seed_physics_failed_and_unknown_binary(self):
        with self.assertRaisesRegex(ValueError,'duplicated'):join.merge(self.base/'bad',[self.a,self.a])
        for mutation in ('seed','physics','failed','binary','datasets','source'):
            with self.subTest(mutation=mutation):
                c=copy.deepcopy(self.cb)
                if mutation=='seed':c['identity']['config']['seed']=self.ca['identity']['config']['seed']
                if mutation=='physics':c['identity']['config']['flux_cm2_s']*=2
                if mutation=='failed':c['status']='failed'
                if mutation=='binary':c['identity']['executable_sha256']='b'*64
                if mutation=='datasets':c['identity']['datasets']['G4LEDATA']['content_sha256']='c'*64
                if mutation=='source':c['identity']['source']['files_sha256']={}
                (self.b/c['attempt']/'run.mac').write_text(macro(c['identity']['config']))
                save(self.b,c)
                with self.assertRaises(ValueError):join.merge(self.base/'bad',[self.a,self.b])
        (self.b/self.cb['attempt']/'run.mac').write_text(macro(self.cb['identity']['config']));save(self.b,self.cb)

    def test_git_analysis_changes_are_harmless_and_transport_changes_rejected(self):
        self.cb['identity']['source']['revision']='a-different-analysis-commit'
        save(self.b,self.cb);join.merge(self.base/'ok',[self.a,self.b])
        self.cb['identity']['environment']['geometry_hash']='different'
        save(self.b,self.cb)
        with self.assertRaises(ValueError):join.merge(self.base/'bad',[self.a,self.b])

    def test_analysis_only_compiled_change_requires_verified_build_evidence(self):
        # Synthetic provenance, never a claim about an actual executable or worker.
        c=copy.deepcopy(self.cb)
        name=next(n for n in c['identity']['source']['files_sha256'] if n.startswith('analysis/') and n.endswith('.cpp'))
        snapshot=self.b/'source'/name
        snapshot.write_text(snapshot.read_text()+'\n// synthetic analysis-only change\n')
        c['identity']['source']['files_sha256'][name]=rt.digest(snapshot)
        compiled=join.build_files(c['identity']['source']['files_sha256'])
        import hashlib
        source_hash=hashlib.sha256(''.join(f'{n}:{h}\n' for n,h in sorted(compiled.items())).encode()).hexdigest()
        old_hash=c['identity']['environment']['source_hash']
        c['identity']['environment']['source_hash']=source_hash
        c['identity']['executable_sha256']='d'*64
        geometry=rt.read(self.b/'geometry.json');geometry['source_hash']=source_hash
        rt.save(self.b/'geometry.json',geometry);c['geometry_sha256']=rt.digest(self.b/'geometry.json')
        log=self.b/c['attempt']/'simulation.log';log.write_text(log.read_text().replace(old_hash,source_hash))
        with uproot.open(self.db) as f: values=f['SimulationMetadata'].arrays(library='np')
        with uproot.update(self.db) as f:
            del f['SimulationMetadata']
            values['SourceHash']=np.array([source_hash],dtype=object)
            f.mktree('SimulationMetadata',test_external.SIMULATION_SCHEMA);f['SimulationMetadata'].extend(values)
        save(self.b,c)
        with self.assertRaisesRegex(ValueError,'compiler/ABI'):join.merge(self.base/'rejected',[self.a,self.b])
        evidence=dict(machine='synthetic',geant4_config_sha256='a'*64,libraries={'libG4synthetic.so':'b'*64},compiler='synthetic',flags=[])
        self.ca['identity']['source']['worker_build']=evidence;save(self.a,self.ca)
        c['identity']['source']['worker_build']=evidence;save(self.b,c)
        joined=join.merge(self.base/'accepted',[self.a,self.b])
        self.assertNotEqual(joined['members'][0]['campaign']['identity']['environment']['source_hash'],
                            joined['members'][1]['campaign']['identity']['environment']['source_hash'])

    def test_accounting_receipt_and_manifest_corruption(self):
        for field in ('AbortedEvents','GeneratedPrimaries'):
            c=copy.deepcopy(self.cb);c['accounting'][field]+=1;save(self.b,c)
            with self.assertRaises(ValueError):join.merge(self.base/'bad',[self.a,self.b])
        save(self.b,self.cb)
        receipt=self.b/self.cb['attempt']/'simulation.command.json'
        rt.save(receipt,dict(returncode=1,command=['rdecay01','--model','cygno-copper-cathode-v4']))
        save(self.b,self.cb)
        with self.assertRaises(ValueError):join.merge(self.base/'bad',[self.a,self.b])


@unittest.skipUnless(shutil.which('root-config'),'ROOT is not installed')
class JoinedRootTests(unittest.TestCase):
    setUp = MergeTests.setUp
    @classmethod
    def setUpClass(cls):
        cls.binary_dir=tempfile.TemporaryDirectory();cls.exe=Path(cls.binary_dir.name)/'AnalyzeExternal'
        subprocess.run(['bash',str(rt.REPO/'external/merge/build_analyzer.sh'),str(cls.exe)],check=True,capture_output=True)
    @classmethod
    def tearDownClass(cls):cls.binary_dir.cleanup()

    def test_native_join_matches_independent_count_reference_and_single(self):
        joined=self.base/'joined';join.merge(joined,[self.a,self.b])
        out=self.base/'analysis'
        result=subprocess.run([str(self.exe),str(joined),str(out)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        counts,windows=spectra(self.canonical)
        scale=self.ca['incident_rate_s']*31536000/2500000000
        with (out/'spectra.tsv').open() as f:
            for row in csv.DictReader(f,delimiter='\t'):
                n=2*counts[row['channel']][int(row['bin'])]
                self.assertEqual(int(row['MC_events']),n)
                self.assertAlmostEqual(float(row['annual_events']),n*scale,delta=max(1e-12,abs(n*scale)*1e-14))
                self.assertAlmostEqual(float(row['annual_variance']),n*scale*scale,delta=max(1e-12,abs(n*scale*scale)*1e-14))
        with (out/'windows.tsv').open() as f:
            for row in csv.DictReader(f,delimiter='\t'):
                self.assertEqual(int(row['positive_MC']),2*windows[row['channel']]['positive'])
                self.assertEqual(int(row['gt10_le400_MC']),2*windows[row['channel']]['gt10_le400'])
        for name in ('analysis.root','spectra.png','spectra.pdf','joined-campaign.json'):
            self.assertGreater((out/name).stat().st_size,0)
        single=subprocess.run([str(self.exe),str(self.a),str(self.base/'single')],capture_output=True,text=True)
        self.assertEqual(single.returncode,0,single.stderr)
        with self.db.open('ab') as f:f.write(b'changed')
        invalid=subprocess.run([str(self.exe),str(joined),str(self.base/'invalid')],capture_output=True,text=True)
        self.assertNotEqual(invalid.returncode,0);self.assertFalse((self.base/'invalid').exists())
