#!/usr/bin/env python3
"""No Geant4/queue required: check dispatch, real runner dry-runs and exit codes."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
site = (repo/'condor/site.conf').read_text()
assert 'request_cpus = $(cpus)' in site and 'CYGNO_JOBS=$(cpus)' in site
assert 'request_memory = 1024 + $(memory_per_process_mb) * $(cpus)' in site
assert 'internal_jobs = 1\n' in site and 'memory_per_process_mb = 4096\n' in site
assert 'on_exit_hold = (ExitBySignal =?= True) || (ExitCode =!= 0)' in site
with tempfile.TemporaryDirectory(prefix='condor-test-') as tmp:
    folder = Path(tmp)
    build, runs = folder/'build with spaces', folder/'runs with spaces'
    build.mkdir()
    runs.mkdir()
    for name in ('rdecay01', 'geometry_quantities'):
        (build/name).symlink_to(shutil.which('true'))
    setup = folder/'activate.sh'
    setup.write_text('export CONDOR_TEST_ACTIVATED=yes\n')
    spy = folder/'python-spy'
    spy.write_text(f'#!{sys.executable}\n' + '''import json, os, sys
from pathlib import Path
if sys.argv[1] == '-c':
    exec(sys.argv[2])
else:
    assert os.environ['CONDOR_TEST_ACTIVATED'] == 'yes'
    Path(os.environ['CONDOR_TEST_ARGS']).write_text(json.dumps(sys.argv[1:]))
    sys.exit(int(os.environ.get('CONDOR_TEST_EXIT', '0')))
''')
    spy.chmod(0o755)
    env = dict(PATH=os.defpath, CYGNO_SRC=str(repo), CYGNO_BUILD=str(build),
               CYGNO_RUNS=str(runs), CYGNO_G4_SETUP=str(setup), CYGNO_PYTHON=str(spy),
               CYGNO_JOBS='13', CYGNO_PRIMARIES='1000000', CYGNO_TAG='1M',
               CYGNO_GAMMA_CONFIG=str(repo/'external/config/hall-c-gamma-2026-proxy.json'),
               CYGNO_NEUTRON_CONFIG=str(repo/'external/config/hall-c-neutron-wulandari-proxy.json'),
               CONDOR_TEST_ARGS=str(folder/'args.json'))

    def invoke(name, **overrides):
        return subprocess.run(['bash', str(repo/'condor/run.sh'), name],
                              env=env | overrides, capture_output=True, text=True)

    for name, count in [('internal-no-gas', 23), ('internal-with-gas', 25),
                        ('external-gamma', 1), ('external-neutron', 1)]:
        result = invoke(name)
        assert result.returncode == 0, result.stderr
        assert 'can write' in result.stdout
        args = json.loads((folder/'args.json').read_text())
        internal = name.startswith('internal-')
        config = (str(repo/'internal/config/study/cygno-11x7-v4.json') if internal else
                  env['CYGNO_GAMMA_CONFIG' if name == 'external-gamma' else 'CYGNO_NEUTRON_CONFIG'])
        expected = ['internal/study/simulate.py' if internal else 'external/study/simulate.py',
                    '--config', config, '--build', str(build), '--output', str(runs/f'{name}-v4-11x7-1M'),
                    '--primaries', '1000000', '--output-mode', 'compact', '--retry-failed']
        if internal:
            expected += ['--jobs', '13', '--gas-bkg', 'yes' if name == 'internal-with-gas' else 'no', '--resume']
        assert args == expected, args
        # Feed the exact dispatched arguments to the real, unchanged CLI parser.
        dry = subprocess.run([sys.executable, *args, '--dry-run'], cwd=repo,
                             capture_output=True, text=True)
        assert dry.returncode == 0, dry.stderr
        assert dry.stdout.count('/run/beamOn 1000000') == count
        submit = (repo/'condor'/f'{name}.sub').read_text()
        assert f'campaign = {name}\n' in submit
        assert 'include : site.conf\nqueue 1\n' in submit
        assert ('cpus = $(internal_jobs)' if internal else 'cpus = 1') in submit
        assert not list(runs.iterdir()), 'Write probes must be removed; dry-runs must not create output'

    for code in (1, 2, 130):
        assert invoke('internal-with-gas', CONDOR_TEST_EXIT=str(code)).returncode == code
    assert invoke('internal-no-gas', CYGNO_JOBS='0').returncode != 0
    assert invoke('external-gamma', CYGNO_RUNS=str(folder/'missing')).returncode != 0
    assert invoke('unknown').returncode != 0
    setup.write_text('return 17\n')
    assert invoke('internal-with-gas').returncode == 17

print('Condor dispatch, 23/25/Hall C dry-runs, resource wiring and failure propagation passed.')
