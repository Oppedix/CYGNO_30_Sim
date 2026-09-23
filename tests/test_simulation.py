import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from study import runtime as rt, simulate
from study.source_matrix import read_matrix


class SimulationTests(unittest.TestCase):
    def test_macros_and_seeds(self):
        rows = read_matrix(rt.REPO/'config/study/thesis-table7.1.json')['contributions']
        self.assertEqual(len(rows), 26)
        cfg = rt.load_config(rt.REPO/'config/study/samuele.json')
        self.assertEqual(cfg['primaries_per_job'], 10_000_000)
        for row in rows:
            for n in [2, 1000, 1_000_000, 10_000_000]:
                macro = rt.macro_for(row, cfg | {'primaries_per_job': n})
                self.assertIn(f'/run/beamOn {n}\n', macro)
                self.assertIn('/rdecay01/fullChain true', macro)
                self.assertIn(rt.RDM_COMMAND, macro)
            self.assertEqual(rt.seeds_for(12345, row['id']), rt.seeds_for(12345, row['id']))
        self.assertNotEqual(rt.seeds_for(12345, rows[0]['id']), rt.seeds_for(12345, rows[1]['id']))

    def test_accounting(self):
        good = dict(RunID=0, RequestedEvents=2, GeneratedPrimaries=2, ProcessedEvents=2, AbortedEvents=0)
        line = 'CYGNO_ACCOUNTING '+json.dumps(good)+'\n'
        self.assertEqual(rt.parse_accounting(line, 2), good)
        self.assertEqual(rt.parse_accounting('G4WT0 > '+line, 2), good)
        for log in ['', line+line, 'CYGNO_ACCOUNTING {}', line.replace('"GeneratedPrimaries": 2', '"GeneratedPrimaries": 1')]:
            with self.assertRaises(ValueError): rt.parse_accounting(log, 2)
        for key in good:
            bad = good | {key: True}
            with self.assertRaises(ValueError): rt.validate_accounting(bad, 2)

    def test_fatal_receipts(self):
        with tempfile.TemporaryDirectory() as d:
            for token in ['PART122', 'FatalException', 'Event must be aborted', 'RunAborted', 'Run aborted']:
                with self.assertRaises(ValueError):
                    rt.invoke([sys.executable, '-c', f'print({token!r})'], Path(d), 'simulation', 5)
                self.assertEqual(rt.read(Path(d)/'simulation.command.json')['returncode'], 0)

    def test_root_free_import(self):
        import subprocess
        code = 'import study.simulate, study.preflight, sys; assert not set(sys.modules) & {"ROOT", "uproot", "awkward", "numpy", "matplotlib"}'
        subprocess.run([sys.executable, '-S', '-c', code], check=True)

    def test_interruption_and_retry(self):
        cfg = rt.load_config(rt.REPO/'config/study/samuele.json') | {'primaries_per_job': 2}
        row = read_matrix(rt.REPO/'config/study/thesis-table7.1.json')['contributions'][0]
        campaign = dict(fingerprint='fixture', identity=dict(effective_environment={}))
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)
            with patch.object(rt, 'invoke', side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt): simulate.run_job(output, row, cfg, campaign, 'unused')
            path = output/'jobs'/row['id']/'manifest.json'
            self.assertEqual(rt.read(path)['status'], 'interrupted')
            with patch.object(rt, 'invoke', side_effect=ValueError('test failure')):
                job = simulate.run_job(output, row, cfg, campaign, 'unused')
                self.assertEqual(job['attempt'], 'attempt-0002')
                self.assertEqual(simulate.run_job(output, row, cfg, campaign, 'unused')['attempt'], 'attempt-0002')
                self.assertEqual(simulate.run_job(output, row, cfg, campaign, 'unused', True)['attempt'], 'attempt-0003')
            self.assertTrue((path.parent/'attempt-0001'/'run.mac').exists())

if __name__ == '__main__': unittest.main()
