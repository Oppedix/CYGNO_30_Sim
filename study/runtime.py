#!/usr/bin/env python3
"""Standard-library provenance, macros and process execution shared by study stages."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import math
import re
import signal
import subprocess
import sys
import threading
import time

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from study.source_matrix import decay_commands, require, LAYOUTS

REPO = Path(__file__).resolve().parents[1]
ENV_KEYS = ('G4NEUTRONHPDATA', 'G4LEDATA', 'G4LEVELGAMMADATA', 'G4RADIOACTIVEDATA',
            'G4PARTICLEXSDATA', 'G4PIIDATA', 'G4REALSURFACEDATA', 'G4SAIDXSDATA',
            'G4ABLADATA', 'G4INCLDATA', 'G4ENSDFSTATEDATA', 'G4CHANNELINGDATA')
RDM_COMMAND = '/process/had/rdm/thresholdForVeryLongDecayTime 1.0e+60 year'
RDM_SECONDS = 1.0e60 * 31536000
LIMITATIONS = ['Smoke samples are software diagnostics, not statistically useful background estimates.',
               'Explicit RDM threshold enables long-lived decays; complete chains require preflight.',
               'Decay preflight validates this environment empirically, not all Geant4 installations.',
               'Historical source sampling and inherited geometry/grouping limitations retained.']


def digest(path):
    with Path(path).open('rb') as file:
        checksum = hashlib.sha256()
        for block in iter(lambda: file.read(1024*1024), b''):
            checksum.update(block)
        return checksum.hexdigest()


def object_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def save(path, value):
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')
    temporary.replace(path)


def read(path):
    return json.loads(path.read_text())


def compiled_source_hash():
    paths = {'CMakeLists.txt', 'analysis/CMakeLists.txt', 'validation/CMakeLists.txt',
             'app/geometry_quantities.cc'}
    for directory, suffixes in {'app': {'.cc'}, 'src': {'.cc'}, 'include': {'.hh'},
                               'common': {'.hh', '.in'}, 'analysis': {'.cpp', '.cc', '.hh'}}.items():
        paths.update(str(p.relative_to(REPO)) for p in (REPO/directory).rglob('*') if p.suffix in suffixes)
    record = ''.join(f'{name}:{digest(REPO/name)}\n' for name in sorted(paths))
    return hashlib.sha256(record.encode()).hexdigest()


def source_state():
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=REPO).decode().strip()
    # Never read/reference-hash local_refs; the matrix already records its citation.
    files = git('ls-files', '-z', '--cached', '--others', '--exclude-standard').split('\0')
    state = {name: digest(REPO/name) if (REPO/name).is_file() else 'missing'
             for name in files if name and Path(name).parts[0] not in ('local_refs', 'local_context')}
    return dict(revision=git('rev-parse', 'HEAD'), branch=git('branch', '--show-current'),
                status=git('status', '--porcelain'), files_sha256=state)


def load_config(path):
    config = read(path)
    require(set(config) == {'schema_version', 'mode', 'layout', 'model', 'source_policy',
                            'primaries_per_job', 'seed', 'timeout_seconds', 'rdm_threshold_years'}, 'Unknown/missing config field')
    require(config['schema_version'] == 1 and config['mode'] in ('smoke', 'production'), 'Mode must be smoke or production')
    require(config['layout'] in LAYOUTS and config['model'] == 'code-compatible' and
            config['source_policy'] == 'historical', 'Unsupported study identity')
    validate_counts(config)
    require(type(config['seed']) is int and 1 <= config['seed'] <= 2_000_000_000, 'Invalid seed')
    require(type(config['timeout_seconds']) is int and config['timeout_seconds'] >= 1,
            'Timeout must be a positive number of seconds')
    require(config['rdm_threshold_years'] == 1e60, 'Study requires explicit RDM threshold 1e60 years')
    return config


def validate_counts(config):
    maximum = 1000 if config['mode'] == 'smoke' else 2_147_483_647
    require(type(config['primaries_per_job']) is int and 1 <= config['primaries_per_job'] <= maximum,
            f"{config['mode']} count must be 1..{maximum} primaries per contribution")


def seeds_for(seed, contribution):
    # Layout is deliberately absent: A/B keep the same seeds for each source.
    value = hashlib.sha256(f'{seed}:{contribution}'.encode()).digest()
    return [int.from_bytes(value[i:i+8], 'big') % 2_000_000_000 + 1 for i in (0, 8)]


def macro_for(row, config):
    seeds = seeds_for(config['seed'], row['id'])
    return '\n'.join([f"# {row['id']}: {config['mode']}; code-compatible / historical",
                      RDM_COMMAND, '/run/printProgress 10000', '/run/verbose 0', '/event/verbose 0', '/tracking/verbose 0',
                      '/random/setSeeds '+' '.join(map(str, seeds)), '/output/OutFile raw',
                      *decay_commands(row), f"/run/beamOn {config['primaries_per_job']}", ''])


_console_lock = threading.Lock()


def console(message):
    """Keep each campaign/progress line intact across invocation threads."""
    with _console_lock:
        print(message, flush=True)


class InvocationCancelled(RuntimeError):
    """The campaign requested that this invocation stop."""


def invoke(command, cwd, label, timeout, *, cancel=None, contribution=None, primaries=None):
    """Durable receipts and child cleanup on Ctrl-C/timeout; never launch a shell."""
    record = dict(command=list(map(str, command)), cwd=str(cwd), started_unix=time.time())
    save(cwd/(label+'.command.json'), record)
    process = None
    try:
        with (cwd/(label+'.log')).open('w') as log:
            if cancel is not None and cancel.is_set():
                raise InvocationCancelled('Campaign interrupted')
            process = subprocess.Popen(record['command'], cwd=cwd, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            last_progress = None
            offset = 0
            with (cwd/(label+'.log')).open() as reader:
                while True:
                    if cancel is not None and cancel.is_set():
                        raise InvocationCancelled('Campaign interrupted')
                    try:
                        process.wait(timeout=min(1., timeout))
                        if cancel is not None and cancel.is_set():
                            raise InvocationCancelled('Campaign interrupted')
                        break
                    except subprocess.TimeoutExpired:
                        if cancel is not None and cancel.is_set():
                            raise InvocationCancelled('Campaign interrupted')
                        if time.time()-record['started_unix'] >= timeout:
                            record['timed_out'] = True
                            raise RuntimeError(f'{label} timed out; retained {cwd}') from None
                        reader.seek(offset)
                        tail = reader.read(); offset = reader.tell()
                        events = re.findall(r'CYGNO_PROGRESS completed_events (\d+)', tail)
                        if events and events[-1] != last_progress:
                            last_progress = events[-1]
                            count = (f'{last_progress}/{primaries} events '
                                     f'({100*int(last_progress)/primaries:.1f}%)'
                                     if primaries else f'{last_progress} events completed')
                            console(f'[{contribution or cwd.name}] {count}')
            record['returncode'] = process.returncode
        text = (cwd/(label+'.log')).read_text(errors='replace')
        require(process.returncode == 0, f'{label} exited {process.returncode}; see {cwd/(label+".log")}')
        require(not any(token in text for token in ('FatalException', 'COMMAND NOT FOUND',
                    '***** Illegal', 'PART122', 'Run must be aborted', 'Event must be aborted', 'RunAborted', 'EventAborted')),
                f'{label} reported a fatal/command/abort error')
        require(not re.search(r'\b(?:run|event)\b[^\n]*\babort(?:ed|ing)\b', text, re.I),
                f'{label} reported an aborted run/event')
        return text
    except (KeyboardInterrupt, InvocationCancelled):
        record['interrupted'] = True
        raise
    finally:
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass  # The child may have exited between poll and killpg.
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            record['returncode'] = process.returncode
        record['finished_unix'] = time.time()
        save(cwd/(label+'.command.json'), record)


def parse_environment(log):
    values = {}
    for line in log.splitlines():
        if line.startswith('CYGNO_ENV '):
            _, key, value = line.split(' ', 2)
            require(key not in values, 'Duplicate environment marker')
            values[key] = value
    required = {*ENV_KEYS, 'source_hash', 'geometry_hash', 'geant4', 'physics', 'radioactive_decay_time_threshold_s'}
    require(set(values) == required and all(values[k] != 'UNRESOLVED' for k in ENV_KEYS),
            'Missing effective physics/data environment')
    require(values['physics'] == 'QGSP_BIC_EMZ+G4RadioactiveDecayPhysics', 'Unexpected physics')
    return values


def dataset_state(environment):
    result = {}
    for key in ENV_KEYS:
        directory = Path(environment[key]).resolve()
        require(directory.is_dir(), f'Missing effective dataset {key}')
        files = sorted(p for p in directory.rglob('*') if p.is_file())
        require(files, f'Empty dataset {key}')
        record = ''.join(f'{p.relative_to(directory)}:{digest(p)}\n' for p in files)
        result[key] = dict(path=str(directory), version_directory=directory.name, files=len(files),
                           content_sha256=hashlib.sha256(record.encode()).hexdigest())
    return result


@contextmanager
def locked(output):
    # Advisory lock is released by the OS on process death; retries never delete a
    # possibly-live lock file. Output is required outside the source checkout.
    require(not output.is_relative_to(REPO), 'Use an output directory outside the source repository')
    output.mkdir(parents=True, exist_ok=True)
    with (output/'.runner.lock').open('a') as file:
        try:
            fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another runner owns this output directory') from None
        yield


def artifacts(directory):
    return {str(p.relative_to(directory)): digest(p) for p in sorted(directory.rglob('*'))
            if p.is_file() and p.name != 'manifest.json'}


def check_artifacts(directory, manifest):
    require(manifest['artifacts'] == artifacts(directory), f'Artifact mismatch: {directory}')


ACCOUNTING_FIELDS = ('RunID', 'RequestedEvents', 'GeneratedPrimaries', 'ProcessedEvents', 'AbortedEvents')


def validate_accounting(values, requested):
    require(set(values) == set(ACCOUNTING_FIELDS) and all(type(x) is int for x in values.values()),
            'Invalid accounting schema')
    require(values == dict(RunID=0, RequestedEvents=requested, GeneratedPrimaries=requested,
                           ProcessedEvents=requested, AbortedEvents=0),
            f'Incomplete/aborted run: {values}; requested {requested}')
    return values


def parse_accounting(log, requested):
    lines = re.findall(r'^(?:G4WT0 > )?CYGNO_ACCOUNTING (.+)$', log, re.M)
    require(len(lines) == 1, 'Need exactly one CYGNO_ACCOUNTING record')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate accounting field')
            result[key] = value
        return result
    return validate_accounting(json.loads(lines[0], object_pairs_hook=unique), requested)


def validate_simulation_log(log, environment, requested):
    require(not any(token in log for token in ('FatalException', 'PART122', 'COMMAND NOT FOUND',
                '***** Illegal', 'RunAborted', 'EventAborted')) and
            not re.search(r'\b(?:run|event)\b[^\n]*\babort(?:ed|ing)\b', log, re.I),
            'Fatal/aborted simulation')
    require(parse_environment(log) == environment, 'Runtime environment changed')
    thresholds = re.findall(r'CYGNO_RUN radioactive_decay_time_threshold_s (\S+)', log)
    require(len(thresholds) == 1 and math.isclose(float(thresholds[0]), RDM_SECONDS, rel_tol=1e-12),
            'Worker did not use required radioactive-decay threshold')
    return parse_accounting(log, requested)
