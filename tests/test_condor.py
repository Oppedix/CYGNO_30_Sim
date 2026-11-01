"""Offline contract tests with explicitly synthetic site responses; never a CNAF submission."""
import io
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from study import runtime as rt
from condor.campaign_transfer import pack,restore
from test_external_merge import completed


class CondorTests(unittest.TestCase):
    def test_frozen_source_provenance_checks_and_dataset_relocation(self):
        from condor.assets import comparable,freeze_source
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();source=root/'source';source.mkdir();(source/'driver.py').write_text('synthetic source')
            (source/'alias.py').symlink_to('driver.py')
            state=dict(revision='a'*40,branch='main',status='',files_sha256={'driver.py':rt.digest(source/'driver.py'),'directory-alias':'missing','alias.py':rt.digest(source/'driver.py')})
            rt.save(source/'.frozen-source.json',state)
            with patch.object(rt,'REPO',source):
                self.assertEqual(rt.source_state(),state)
                destination=root/'snapshot';destination.mkdir();freeze_source(destination,state)
                self.assertEqual((destination/'alias.py').read_bytes(),(source/'driver.py').read_bytes())
                self.assertFalse((destination/'alias.py').is_symlink())
                self.assertFalse((destination/'directory-alias').exists())
                (source/'driver.py').write_text('changed')
                with self.assertRaisesRegex(ValueError,'snapshot mismatch'):rt.source_state()
        a=dict(environment={'geant4':'synthetic','G4LEDATA':'/prepare/data'},source_radius_mm=1,
               datasets={'G4LEDATA':dict(path='/prepare/data',files=2,content_sha256='synthetic')})
        b=dict(environment={'geant4':'synthetic','G4LEDATA':'/worker/data'},source_radius_mm=1,
               datasets={'G4LEDATA':dict(path='/worker/data',files=2,content_sha256='synthetic')})
        self.assertEqual(comparable(a),comparable(b))
        b['datasets']['G4LEDATA']['content_sha256']='different'
        self.assertNotEqual(comparable(a),comparable(b))

    def test_shell_syntax_and_exact_site_interface(self):
        for script in (rt.REPO/'condor').glob('*.sh'):
            subprocess.run(['bash','-n',str(script)],check=True)
        text=(rt.REPO/'condor/subber_geant4.sh').read_text()
        self.assertIn('source /cvmfs/sft-cygno.infn.it/config/lib/subcreator.sh',text)
        self.assertIn('source /cvmfs/sft-cygno.infn.it/config/cygno_htc -s "$CONFOUTPATH/sub" "$CE"',text)
        self.assertNotIn('condor_submit',text)
        self.assertFalse(list((rt.REPO/'condor').glob('*.sub')))
        for particle,config in [('gamma','hall-c-gamma-2026-proxy.json'),('neutron','hall-c-neutron-wulandari-proxy.json')]:
            dry=subprocess.run([os.sys.executable,str(rt.REPO/'external/study/simulate.py'),'--config',str(rt.REPO/'external/config'/config),
                                '--primaries','1000000000','--seed','730000001','--dry-run'],capture_output=True,text=True)
            self.assertEqual(dry.returncode,0,dry.stderr);self.assertIn('/run/beamOn 1000000000',dry.stdout)

    def test_complete_transfer_roundtrip_no_overwrite_tamper_and_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);source=base/'campaign';completed(source)
            archive=base/'sample.tar';pack(source,archive)
            before={str(p.relative_to(source)):rt.digest(p) for p in source.rglob('*') if p.is_file()}
            target=base/'restored';restore(archive,target)
            self.assertEqual(before,{str(p.relative_to(target)):rt.digest(p) for p in target.rglob('*') if p.is_file()})
            with self.assertRaises(ValueError):restore(archive,target)
            with archive.open('ab') as f:f.write(b'tampered')
            with self.assertRaises(ValueError):restore(archive,base/'bad')
            evil=base/'evil.tar'
            with tarfile.open(evil,'w') as f:
                member=tarfile.TarInfo('campaign/../../escaped');member.size=1;f.addfile(member,io.BytesIO(b'x'))
            evil.with_name(evil.name+'.sha256').write_text(rt.digest(evil)+'  '+evil.name+'\n')
            with self.assertRaises(ValueError):restore(evil,base/'unsafe')
            self.assertFalse((base/'escaped').exists())

    def setup_site(self,base):
        scripts=base/'scripts';scripts.mkdir();assets=base/'assets';assets.mkdir()
        (assets/'worker-assets.tar').write_bytes(b'synthetic-asset-not-a-worker')
        (assets/'worker-assets.tar.sha256').write_text(rt.digest(assets/'worker-assets.tar')+'  worker-assets.tar\n')
        (assets/'run_geant4_worker.sh').write_text('# synthetic worker fixture\n')
        (assets/'submission-assets.sha256').write_text((assets/'worker-assets.tar.sha256').read_text()+rt.digest(assets/'run_geant4_worker.sh')+'  run_geant4_worker.sh\n')
        creator=base/'subcreator.sh'
        creator.write_text('''[[ $CPUs == 1 && $BACKET == cygno-sim && $EXECUTE == run_geant4_worker.sh ]]
[[ ${#FILENAMES[@]} == 2 && ${FILENAMES[0]} == *.tar && ${FILENAMES[1]} == *.tar.sha256 ]]
printf '%s %s %s %s\\n' "$BATCHNAME" "$ARGUMENTS" "$TAG" "$CE" >> "$TEST_CALLS"
export CONFOUTPATH=/synthetic
''')
        submit=base/'cygno_htc'
        submit.write_text('''[[ $1 == -s && $2 == /synthetic/sub ]]
if [[ $BATCHNAME == *r03 && ${TEST_FAIL:-0} == 1 ]]; then echo 'SYNTHETIC ambiguous failure' >&2; return 19; fi
echo 'SYNTHETIC job identifier 123.0'
''')
        for name in ('subber_geant4.sh','submit_replicas.sh'):
            text=(rt.REPO/'condor'/name).read_text().replace('/cvmfs/sft-cygno.infn.it/config/lib/subcreator.sh',str(creator)).replace('/cvmfs/sft-cygno.infn.it/config/cygno_htc',str(submit))
            (scripts/name).write_text(text)
        env=os.environ | dict(CYGNO_ASSETS=str(assets),CYGNO_SUBMISSIONS=str(base/'state'),TEST_CALLS=str(base/'calls'))
        return scripts,env

    def test_nine_independent_requests_ids_seeds_destinations_and_retry_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);scripts,env=self.setup_site(base)
            command=['bash',str(scripts/'submit_replicas.sh'),'gamma','9','1000000000','2']
            r=subprocess.run(command,env=env,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            calls=(base/'calls').read_text().splitlines();self.assertEqual(len(calls),9)
            self.assertEqual(r.stdout.count('SYNTHETIC job identifier'),9)
            for i,line in enumerate(calls,1):
                self.assertIn(str(730000000+i),line);self.assertIn(f'r{i:02}',line)
            retry=subprocess.run(command,env=env,capture_output=True,text=True)
            self.assertNotEqual(retry.returncode,0);self.assertIn('already reserved',retry.stderr)
            self.assertEqual((base/'calls').read_text().splitlines(),calls)

    def test_partial_failure_preserves_reservations_and_reports_uncertainty(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);scripts,env=self.setup_site(base);env['TEST_FAIL']='1'
            r=subprocess.run(['bash',str(scripts/'submit_replicas.sh'),'gamma','9','1000000000','3'],env=env,capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0);self.assertIn('STOPPED at replica 3/9',r.stderr)
            self.assertIn('FAILED/UNCERTAIN',r.stderr)
            self.assertEqual(len((base/'calls').read_text().splitlines()),3)
            self.assertEqual(len(list((base/'state/seeds').iterdir())),3)
            self.assertFalse(list((base/'state').glob('*r04')))

    def test_corrupt_worker_asset_fails_before_unpack(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'worker-assets.tar').write_bytes(b'corrupted')
            r=subprocess.run(['bash',str(rt.REPO/'condor/run_geant4_worker.sh'),'0'*64,'gamma','sample','2','42'],cwd=root,capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0);self.assertFalse((root/'runtime').exists())
