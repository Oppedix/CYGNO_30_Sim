from contextlib import redirect_stdout, redirect_stderr
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
from study import runtime as rt, simulate
from study.campaign import validate_campaign
from study.source_matrix import COMPONENTS, read_matrix


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

    def test_main_error_and_interrupt_exit_status(self):
        for error, status in [(ValueError('configuration/preflight failure'), 1), (KeyboardInterrupt(), 130)]:
            with self.subTest(status=status), patch.object(simulate, 'run', side_effect=error), \
                 patch.object(sys, 'argv', ['simulate.py']), redirect_stderr(io.StringIO()):
                self.assertEqual(simulate.main(), status)

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

class SchedulingTests(unittest.TestCase):
    """Synthetic transport only: exercise real job manifests and accounting."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name)
        self.cfg = rt.load_config(rt.REPO/'config/study/samuele.json') | {'primaries_per_job': 2}
        self.matrix = read_matrix(rt.REPO/'config/study/thesis-table7.1.json')
        self.rows = self.matrix['contributions']
        self.env = dict.fromkeys(rt.ENV_KEYS, '/fixture/data') | dict(
            source_hash='fixture-source', geometry_hash=rt.digest(rt.REPO/'common/DetectorGeometry.hh'),
            geant4='fixture', physics='QGSP_BIC_EMZ+G4RadioactiveDecayPhysics',
            radioactive_decay_time_threshold_s=str(rt.RDM_SECONDS))
        identity = dict(config=self.cfg, matrix=self.matrix, effective_environment=self.env)
        self.campaign = dict(schema_version=2, stage='simulation', identity=identity,
                             fingerprint=rt.object_digest(identity))
        rt.save(self.output/'matrix.json', self.matrix)
        self.stream = io.StringIO()
        redirect = redirect_stdout(self.stream)
        redirect.__enter__()
        self.addCleanup(redirect.__exit__, None, None, None)

    def fake_invoke(self, command, cwd, label, timeout, **options):
        self.assertEqual(command[2], '1')
        self.assertEqual(options['contribution'], cwd.parent.name)
        count = options['primaries']
        log = '\n'.join(f'CYGNO_ENV {k} {v}' for k, v in self.env.items())+'\n'
        log += f'CYGNO_RUN radioactive_decay_time_threshold_s {rt.RDM_SECONDS}\n'
        log += 'CYGNO_ACCOUNTING '+json.dumps(dict(RunID=0, RequestedEvents=count,
            GeneratedPrimaries=count, ProcessedEvents=count, AbortedEvents=0))+'\n'
        (cwd/'outfiles_V2').mkdir()
        (cwd/'outfiles_V2/raw.root').write_bytes(b'Synthetic nonempty file; Stage A does not inspect ROOT')
        (cwd/(label+'.log')).write_text(log)
        rt.save(cwd/(label+'.command.json'), dict(command=list(map(str, command)), returncode=0))
        return log

    def schedule(self, rows=None, **options):
        try:
            simulate.schedule_jobs(self.output, self.rows if rows is None else rows, self.cfg,
                                   self.campaign, self.matrix, 'fixture', **options)
        finally:
            simulate.update_campaign(self.output, self.campaign, self.matrix)

    def manifest(self, row):
        return rt.read(self.output/'jobs'/row['id']/'manifest.json')

    def test_default_jobs_and_positive_integer(self):
        self.assertEqual(simulate.parser().parse_args([]).jobs, 1)
        for value in ('0', '-1', '1.5', 'invalid'):
            with self.subTest(value=value), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                simulate.parser().parse_args(['--jobs', value])
        calls = []
        def invoke(*args, **options):
            # The previous job must be durable before the next invocation begins.
            for previous in calls:
                self.assertEqual(self.manifest(previous)['status'], 'complete')
            calls.append(next(row for row in self.rows if row['id'] == options['contribution']))
            return self.fake_invoke(*args, **options)
        with patch.object(rt, 'invoke', side_effect=invoke):
            self.schedule(self.rows[:4])
        self.assertEqual(calls, self.rows[:4])

    def test_bounded_overlap_and_main_thread_aggregation(self):
        barrier = threading.Barrier(3)
        lock = threading.Lock()
        active = peak = 0
        def invoke(*args, **options):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            try:
                barrier.wait(timeout=10)  # Six jobs in two groups; no sleeps.
                return self.fake_invoke(*args, **options)
            finally:
                with lock:
                    active -= 1
        original_save = rt.save
        def save(path, value):
            if path.name == 'campaign.json':
                self.assertIs(threading.current_thread(), threading.main_thread())
            original_save(path, value)
        with patch.object(rt, 'invoke', side_effect=invoke), patch.object(rt, 'save', side_effect=save):
            self.schedule(self.rows[:6], jobs=3)
        self.assertEqual(peak, 3)
        self.assertEqual(self.campaign['coverage'], '6/26')
        self.assertIn('[DONE 6/6]', self.stream.getvalue())
        with patch('study.campaign.validate_snapshots'), patch('study.campaign.validate_preflight'):
            self.assertEqual(len(validate_campaign(self.output, allow_partial=True)), 6)

    def test_reuse_and_cap_to_runnable_contributions(self):
        with patch.object(rt, 'invoke', side_effect=self.fake_invoke):
            self.schedule(self.rows[:1])
        previous = rt.artifacts(self.output/'jobs'/self.rows[0]['id'])
        with patch.object(rt, 'invoke', side_effect=self.fake_invoke) as invoke, \
             patch.object(simulate, 'ThreadPoolExecutor', wraps=simulate.ThreadPoolExecutor) as pool:
            self.schedule(self.rows[:3], jobs=16)
        pool.assert_called_once_with(max_workers=2)
        self.assertEqual(invoke.call_count, 2)
        self.assertEqual(previous, rt.artifacts(self.output/'jobs'/self.rows[0]['id']))
        with patch.object(rt, 'invoke') as invoke:
            self.schedule(self.rows[:3], jobs=16)
        invoke.assert_not_called()
        self.assertIn('[REUSE 3/3]', self.stream.getvalue())

    def test_failure_continues_matrix_and_requires_retry(self):
        failed = self.rows[0]
        def invoke(*args, **options):
            if options['contribution'] == failed['id']:
                raise RuntimeError('synthetic transport failure')
            return self.fake_invoke(*args, **options)
        with patch.object(rt, 'invoke', side_effect=invoke):
            self.schedule(jobs=4)
        self.assertEqual(self.campaign['coverage'], '25/26')
        self.assertEqual(self.manifest(failed)['status'], 'failed')
        with patch.object(rt, 'invoke') as invoke:
            self.schedule(jobs=4)
        invoke.assert_not_called()
        with patch.object(rt, 'invoke', side_effect=self.fake_invoke) as invoke:
            self.schedule(jobs=4, retry=True)
        self.assertEqual(invoke.call_count, 1)
        self.assertEqual(self.manifest(failed)['attempt'], 'attempt-0002')
        self.assertEqual(self.campaign['coverage'], '26/26')
        with patch('study.campaign.validate_snapshots'), patch('study.campaign.validate_preflight'):
            self.assertEqual(len(validate_campaign(self.output)), 26)

    def test_interrupt_drains_active_jobs_leaves_pending_and_resumes(self):
        with patch.object(rt, 'invoke', side_effect=self.fake_invoke):
            self.schedule(self.rows[:1])
        completed = self.manifest(self.rows[0])
        ready = threading.Barrier(3)
        started = []
        lock = threading.Lock()
        def invoke(*args, cancel, **options):
            with lock:
                started.append(options['contribution'])
            ready.wait(timeout=10)
            self.assertTrue(cancel.wait(timeout=10))
            raise rt.InvocationCancelled('test cancellation')
        def interrupt(*args, **kwargs):
            ready.wait(timeout=10)  # Both invocations are active before Ctrl-C.
            raise KeyboardInterrupt
        original_handler = signal.getsignal(signal.SIGINT)
        original_shutdown = simulate.ThreadPoolExecutor.shutdown
        def shutdown(pool, **kwargs):
            self.assertEqual(signal.getsignal(signal.SIGINT), signal.SIG_IGN)
            signal.raise_signal(signal.SIGINT)  # A second Ctrl-C cannot abort cleanup.
            return original_shutdown(pool, **kwargs)
        with patch.object(rt, 'invoke', side_effect=invoke), patch.object(simulate, 'wait', side_effect=interrupt), \
             patch.object(simulate.ThreadPoolExecutor, 'shutdown', shutdown):
            with self.assertRaises(KeyboardInterrupt):
                self.schedule(self.rows[:5], jobs=2)
        self.assertEqual(signal.getsignal(signal.SIGINT), original_handler)
        self.assertCountEqual(started, [row['id'] for row in self.rows[1:3]])
        self.assertEqual(self.manifest(self.rows[0]), completed)
        for row in self.rows[1:3]:
            self.assertEqual(self.manifest(row)['status'], 'interrupted')
        for row in self.rows[3:5]:
            self.assertFalse((self.output/'jobs'/row['id']).exists())
            self.assertEqual(self.campaign['job_records'][row['id']]['status'], 'not_started')
        attempts = {row['id']: (self.output/'jobs'/row['id']/'attempt-0001'/'manifest.json').read_bytes()
                    for row in self.rows[1:3]}
        with patch.object(rt, 'invoke', side_effect=self.fake_invoke):
            self.schedule(self.rows[:5], jobs=3)
        for row in self.rows[1:3]:
            self.assertEqual(self.manifest(row)['attempt'], 'attempt-0002')
            self.assertEqual((self.output/'jobs'/row['id']/'attempt-0001'/'manifest.json').read_bytes(),
                             attempts[row['id']])
        self.assertEqual(self.campaign['coverage'], '5/26')

    def test_precancelled_job_never_creates_attempt(self):
        cancel = threading.Event()
        cancel.set()
        with patch.object(rt, 'invoke') as invoke, self.assertRaises(rt.InvocationCancelled):
            simulate.run_job(self.output, self.rows[0], self.cfg, self.campaign, 'fixture', cancel=cancel)
        invoke.assert_not_called()
        self.assertFalse((self.output/'jobs').exists())

    def test_scheduling_preserves_macros_seeds_and_fingerprints(self):
        with patch.object(rt, 'invoke', side_effect=self.fake_invoke):
            self.schedule(jobs=1)
            sequential = {row['id']: self.manifest(row) for row in self.rows}
            macros = {row['id']: (self.output/'jobs'/row['id']/'attempt-0001/run.mac').read_bytes()
                      for row in self.rows}
            self.output = self.output/'parallel'
            self.output.mkdir()
            self.schedule(jobs=16)
        for row in self.rows:
            job = self.manifest(row)
            for key in ('fingerprint', 'campaign_fingerprint', 'seeds', 'workers', 'macro_sha256'):
                self.assertEqual(job[key], sequential[row['id']][key])
            self.assertEqual(job['workers'], 1)
            self.assertEqual((self.output/'jobs'/row['id']/'attempt-0001/run.mac').read_bytes(), macros[row['id']])
        self.assertEqual(rt.object_digest(self.campaign['identity']), self.campaign['fingerprint'])

    def test_cli_jobs_only_resume_preflight_and_exit_status(self):
        build = self.output/'build'
        build.mkdir()
        for name in ('rdecay01', 'geometry_quantities', 'CMakeCache.txt'):
            (build/name).write_text('fixture')
        def invoke(command, cwd, label, timeout, **options):
            if label == 'environment':
                return '\n'.join(f'CYGNO_ENV {k} {v}' for k, v in self.env.items())
            if label == 'quantities':
                headers = dict(layout=self.cfg['layout'], **{'detector-model': 'code-compatible',
                    'source-policy': 'historical', 'geometry-hash': self.env['geometry_hash'],
                    'compiled-source-hash': self.env['source_hash'], 'provenance': 'synthetic test'})
                Path(command[1]).write_text(''.join(f'# {k}: {v}\n' for k, v in headers.items())+
                    'component\tmass_kg\tpieces\tgeometry_material\n'+
                    ''.join(f'{name}\t2\t3\tfixture\n' for name in COMPONENTS))
                rt.save(Path(command[3]), dict(layout=self.cfg['layout'], geometry_hash=self.env['geometry_hash'],
                    source_hash=self.env['source_hash'], gas_size_mm=[100, 100, 100],
                    gas_centers_mm={str(i): [0, 0, 0] for i in range(150)}))
                return ''
            return self.fake_invoke(command, cwd, label, timeout, **options)
        def preflight(build, folder):
            folder.mkdir()
            rt.save(folder/'preflight.json', dict(complete=True, checks={
                name: dict(status='passed', PART122=False, environment=self.env)
                for name in ('u238-default', 'u238-enabled', 'th232-full', 'bi212-full')}))
        ids = [row['id'] for row in self.rows[:3]]
        args = simulate.parser().parse_args(['--build', str(build), '--output', str(self.output/'campaign'),
                                            '--primaries', '2', '--only', *ids])
        with patch.object(rt, 'invoke', side_effect=invoke) as invoked, \
             patch.object(rt, 'dataset_state', return_value={}), \
             patch.object(rt, 'source_state', return_value={'files_sha256': {}}), \
             patch.object(rt, 'compiled_source_hash', return_value=self.env['source_hash']), \
             patch('study.preflight.check', side_effect=preflight) as checked:
            self.assertEqual(simulate.run(args), 2)
            original = rt.read(args.output/'campaign.json')
            args.jobs = 16
            args.only = ids + [self.rows[3]['id']]
            self.assertEqual(simulate.run(args), 2)
            resumed = rt.read(args.output/'campaign.json')
            self.assertEqual(resumed['identity'], original['identity'])
            self.assertEqual(resumed['fingerprint'], original['fingerprint'])
            self.assertEqual(resumed['coverage'], '4/26')
            self.assertEqual(len(list((args.output/'jobs').iterdir())), 4)
            checked.assert_called_once()
            self.assertEqual(sum(call.args[2] == 'simulation' for call in invoked.call_args_list), 4)
            args.only = None
            self.assertEqual(simulate.run(args), 0)
            self.assertEqual(len(validate_campaign(args.output)), 26)


class InvocationTests(unittest.TestCase):
    def test_cancel_terminates_real_child_and_records_interruption(self):
        cancel = threading.Event()
        started = threading.Event()
        children = []
        errors = []
        original_popen = subprocess.Popen
        def popen(*args, **kwargs):
            child = original_popen(*args, **kwargs)
            children.append(child)
            started.set()
            return child
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path(directory)
            def invoke():
                try:
                    rt.invoke([sys.executable, '-c', 'import time; time.sleep(60)'], cwd,
                              'simulation', 120, cancel=cancel)
                except BaseException as error:
                    errors.append(error)
            with patch.object(rt.subprocess, 'Popen', side_effect=popen):
                thread = threading.Thread(target=invoke)
                thread.start()
                try:
                    self.assertTrue(started.wait(timeout=10))
                finally:
                    cancel.set()
                    thread.join(timeout=10)
                    # Even a regression must not leave a test helper behind.
                    for child in children:
                        if child.poll() is None:
                            os.killpg(child.pid, signal.SIGKILL)
                            child.wait()
                    thread.join(timeout=10)
            self.assertFalse(thread.is_alive())
            self.assertEqual(len(errors), 1)
            self.assertIsInstance(errors[0], rt.InvocationCancelled)
            self.assertIsNotNone(children[0].poll())
            receipt = rt.read(cwd/'simulation.command.json')
            self.assertTrue(receipt['interrupted'])
            self.assertNotEqual(receipt['returncode'], 0)

    def test_cancellation_kill_fallback_and_receipt(self):
        cancel = threading.Event()
        process = Mock(pid=123, returncode=None)
        process.poll.return_value = None
        def wait(timeout=None):
            if timeout == 1:
                cancel.set()
                raise subprocess.TimeoutExpired('fixture', timeout)
            if timeout == 5:
                raise subprocess.TimeoutExpired('fixture', timeout)
            process.returncode = -signal.SIGKILL
        process.wait.side_effect = wait
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(rt.subprocess, 'Popen', return_value=process), patch.object(rt.os, 'killpg') as kill:
            cwd = Path(directory)
            with self.assertRaises(rt.InvocationCancelled):
                rt.invoke(['fixture'], cwd, 'simulation', 120, cancel=cancel)
            self.assertEqual([call.args for call in kill.call_args_list],
                             [(123, signal.SIGTERM), (123, signal.SIGKILL)])
            receipt = rt.read(cwd/'simulation.command.json')
            self.assertTrue(receipt['interrupted'])
            self.assertEqual(receipt['returncode'], -signal.SIGKILL)
            self.assertNotIn('timed_out', receipt)

    def test_progress_identifies_contribution_and_percentage(self):
        process = Mock(returncode=0)
        process.wait.side_effect = [subprocess.TimeoutExpired('fixture', 1), 0]
        process.poll.return_value = 0
        def popen(*args, **kwargs):
            kwargs['stdout'].write('CYGNO_PROGRESS completed_events 500\n')
            kwargs['stdout'].flush()
            return process
        with tempfile.TemporaryDirectory() as directory, patch.object(rt.subprocess, 'Popen', side_effect=popen):
            stream = io.StringIO()
            with redirect_stdout(stream):
                rt.invoke(['fixture'], Path(directory), 'simulation', 120,
                          contribution='GEMsCore_U238', primaries=1000)
            self.assertEqual(stream.getvalue(), '[GEMsCore_U238] 500/1000 events (50.0%)\n')


if __name__ == '__main__': unittest.main()
