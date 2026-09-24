#!/usr/bin/env python3
"""Stage A: standard-library-only, resumable Table 7.1 simulation campaigns."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import hashlib
import math
import os
from pathlib import Path
import platform
import shutil
import signal
import sys
import threading
import time

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from study import runtime as rt
from study.source_matrix import read_matrix, read_quantities, require


def needs_attempt(previous, retry):
    return (previous is None or previous['status'] in ('running', 'interrupted') or
            (previous['status'] != 'complete' and retry))


def run_job(output, row, config, campaign, simulation, retry=False, cancel=None):
    if cancel is not None and cancel.is_set():
        raise rt.InvocationCancelled('Campaign interrupted before contribution started')
    directory = output/'jobs'/row['id']
    directory.mkdir(parents=True, exist_ok=True)
    path = directory/'manifest.json'
    macro = rt.macro_for(row, config)
    fingerprint = rt.object_digest(dict(campaign=campaign['fingerprint'], contribution=row, macro=macro))
    previous = rt.read(path) if path.exists() else None
    if previous:
        require(previous['fingerprint'] == fingerprint, 'Job identity mismatch: '+row['id'])
        if previous['status'] == 'complete':
            from study.campaign import validate_job
            validate_job(output, row, campaign)
            return previous
        if not needs_attempt(previous, retry):
            return previous
    # Max rather than count tolerates gaps without ever overwriting an attempt.
    number = max([int(p.name[8:]) for p in directory.glob('attempt-*')] or [0])+1
    attempt = directory/f'attempt-{number:04d}'
    attempt.mkdir()
    manifest = dict(schema_version=campaign.get('schema_version',3), fingerprint=fingerprint, contribution=row['id'],
                    campaign_fingerprint=campaign['fingerprint'], attempt=attempt.name, status='running',
                    seeds=rt.seeds_for(config['seed'], row['id']), workers=1,
                    requested_primaries=config['primaries_per_job'], generated_primaries=None,
                    macro_sha256=hashlib.sha256(macro.encode()).hexdigest(), chain_validity='environment-preflight-passed',
                    previous_attempt=previous['attempt'] if previous else None)
    if campaign.get('schema_version',3) >= 3:
        manifest.update(output_mode=config.get('output_mode','raw'), output_schema_version=1,
                        data_path=None, parity_status='pending-stage-b' if config.get('output_mode')=='both' else 'not-applicable')
    rt.save(path, manifest)
    try:
        rt.console('[START] '+row['id'])
        (attempt/'run.mac').write_text(macro)
        log = rt.invoke([simulation, attempt/'run.mac', '1', '--layout', config['layout'],
                         '--output-mode', config.get('output_mode','raw')],
                        attempt, 'simulation', config['timeout_seconds'], cancel=cancel,
                        contribution=row['id'], primaries=config['primaries_per_job'])
        manifest['accounting'] = rt.validate_simulation_log(
            log, campaign['identity']['effective_environment'], config['primaries_per_job'])
        roots = list((attempt/'outfiles_V2').glob('*.root'))
        mode = config.get('output_mode','raw')
        require(len(roots) == 1 and roots[0].name in (mode+'.root', mode+'_t0.root') and
                roots[0].stat().st_size > 0, 'Expected one nonempty serial/single-worker output file')
        manifest['data_path' if manifest['schema_version']>=3 else 'raw_path'] = str(roots[0].relative_to(attempt))
        manifest.update(generated_primaries=manifest['accounting']['GeneratedPrimaries'], status='complete')
    except KeyboardInterrupt:
        manifest.update(status='interrupted', error='Interrupted; repeat command to resume')
        raise
    except rt.InvocationCancelled:
        manifest.update(status='interrupted', error='Interrupted; repeat command to resume')
    except (ValueError, RuntimeError, OSError) as error:
        manifest.update(status='failed', error=str(error), chain_validity='incomplete')
    finally:
        manifest['artifacts'] = rt.artifacts(attempt)
        rt.save(attempt/'manifest.json', manifest)
        rt.save(path, manifest)
    return manifest


def update_campaign(output, campaign, matrix):
    records = {}
    for row in matrix['contributions']:
        path = output/'jobs'/row['id']/'manifest.json'
        records[row['id']] = rt.read(path) if path.exists() else dict(status='not_started')
    campaign['job_records'] = records
    completed = sum(job['status'] == 'complete' for job in records.values())
    campaign.update(coverage=f'{completed}/26', status='complete' if completed == 26 else 'incomplete',
                    scientific_validity='raw-accounting-complete; offline-validation-required' if completed == 26
                    else 'incomplete; not a full-matrix result')
    rt.save(output/'campaign.json', campaign)


def schedule_jobs(output, rows, config, campaign, matrix, simulation, jobs=1, retry=False):
    """Run on the main thread under the campaign lock; workers own job directories."""
    completed = 0

    def report(row, job, reused=False):
        nonlocal completed
        if job['status'] == 'complete':
            completed += 1
            label = 'REUSE' if reused else 'DONE'
            rt.console(f"[{label} {completed}/{len(rows)}] {row['id']}")
        else:
            label = 'RETAIN' if reused else job['status'].upper()
            detail = ' (use --retry-failed)' if reused else ': '+job.get('error', '')
            rt.console(f"[{label}] {row['id']}{detail} ({completed}/{len(rows)} complete)")
        update_campaign(output, campaign, matrix)

    rt.console(f"Campaign: {len(rows)} contributions, jobs={jobs}, primaries={config['primaries_per_job']}")
    pending = []
    for row in rows:
        path = output/'jobs'/row['id']/'manifest.json'
        previous = rt.read(path) if path.exists() else None
        if needs_attempt(previous, retry):
            pending.append(row)
        else:
            # Validate/reuse on the main thread before launching any new work.
            report(row, run_job(output, row, config, campaign, simulation, retry), reused=True)
    if not pending:
        return

    cancel = threading.Event()
    limit = min(jobs, len(pending))
    pool = ThreadPoolExecutor(max_workers=limit)
    active = {}
    remaining = iter(pending)
    try:
        while True:
            # Submit only enough to fill free slots, never the entire matrix.
            while len(active) < limit and not cancel.is_set():
                row = next(remaining, None)
                if row is None:
                    break
                future = pool.submit(run_job, output, row, config, campaign, simulation, retry, cancel)
                active[future] = row
            if not active:
                break
            done, _ = wait(active, return_when=FIRST_COMPLETED)
            for future in done:
                row = active.pop(future)
                report(row, future.result())
    finally:
        # KeyboardInterrupt reaches this thread, not invoke() in pool threads.
        # Set the event BEFORE joining, and keep the campaign lock until all
        # process groups are reaped and all attempt manifests are durable.
        cancel.set()
        # A second Ctrl-C must not interrupt thread joins and abandon children.
        handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            pool.shutdown(wait=True, cancel_futures=True)
            for future, row in active.items():
                if not future.cancelled() and future.exception() is None:
                    report(row, future.result())
        finally:
            signal.signal(signal.SIGINT, handler)


def run(args):
    config = rt.load_config(args.config)
    config.update(output_mode=args.output_mode, output_schema_version=1)
    if args.mode:
        config.update(mode=args.mode, primaries_per_job=2 if args.mode == 'smoke' else 10_000_000)
    if args.primaries is not None:
        config['primaries_per_job'] = args.primaries
    # Statistics are independent of chain completeness and diagnostic labeling.
    require(type(config['primaries_per_job']) is int and 1 <= config['primaries_per_job'] <= 2_147_483_647,
            'Primaries must be 1..2147483647')
    matrix = read_matrix(args.matrix)
    selected = set(args.only or [r['id'] for r in matrix['contributions']])
    require(selected <= {r['id'] for r in matrix['contributions']}, 'Unknown --only contribution')
    if args.list or args.macros_dir:
        if args.macros_dir:
            args.macros_dir.mkdir(parents=True, exist_ok=False)
            rt.save(args.macros_dir/'config.json', config)
        for row in matrix['contributions']:
            if row['id'] in selected:
                macro = rt.macro_for(row, config)
                print(macro)
                if args.macros_dir:
                    (args.macros_dir/(row['id']+'.mac')).write_text(macro)
        return 0
    require(args.build is not None and args.output is not None, '--build and --output are required')
    output, build = args.output.resolve(), args.build.resolve()
    tools = {key: build/name for key, name in [('simulation', 'rdecay01'), ('quantities', 'geometry_quantities')]}
    require(all(p.is_file() for p in tools.values()), 'Build rdecay01 and geometry_quantities first')
    with rt.locked(output):
        probe = output/'probes'/f'probe-{time.time_ns()}'
        probe.mkdir(parents=True)
        (probe/'environment.mac').write_text(rt.RDM_COMMAND+'\n/control/echo CYGNO_ENVIRONMENT_PROBE\n')
        environment = rt.parse_environment(rt.invoke([tools['simulation'], probe/'environment.mac', '1',
                '--layout', config['layout']], probe, 'environment', config['timeout_seconds']))
        require(math.isclose(float(environment['radioactive_decay_time_threshold_s']), rt.RDM_SECONDS, rel_tol=1e-12),
                'Incorrect effective radioactive-decay threshold')
        require(environment['source_hash'] == rt.compiled_source_hash(), 'Stale compiled source; rebuild')
        require(environment['geometry_hash'] == rt.digest(rt.REPO/'common/DetectorGeometry.hh'), 'Stale geometry build')
        identity = dict(config=config, matrix=matrix, source=rt.source_state(),
            build_tools={k: dict(path=str(v), sha256=rt.digest(v)) for k, v in tools.items()},
            cmake_cache_sha256=rt.digest(build/'CMakeCache.txt'), effective_environment=environment,
            datasets=rt.dataset_state(environment),
            execution_environment={k: v for k, v in sorted(os.environ.items())
                if k.startswith(('G4', 'GEANT4', 'DYLD_', 'LD_')) or k in ('ROOTSYS', 'OMP_NUM_THREADS')},
            python=sys.version, python_executable=sys.executable, platform=platform.platform())
        fingerprint = rt.object_digest(identity)
        path = output/'campaign.json'
        if path.exists():
            campaign = rt.read(path)
            require(campaign['schema_version'] == 3 and campaign['fingerprint'] == fingerprint and
                    campaign['identity'] == identity, 'Campaign identity changed; use a new output directory')
        else:
            require(not (output/'jobs').exists(), 'Orphan jobs without campaign manifest')
            rt.invoke([tools['quantities'], probe/'quantities.tsv', config['layout'], probe/'geometry.json'],
                      probe, 'quantities', config['timeout_seconds'])
            require(f"# compiled-source-hash: {environment['source_hash']}" in (probe/'quantities.tsv').read_text().splitlines(),
                    'Stale quantity exporter')
            for name in ('quantities.tsv', 'geometry.json'):
                shutil.copyfile(probe/name, output/name)
            quantities = read_quantities(output/'quantities.tsv', layout=config['layout'], model=config['model'],
                                         geometry_hash=environment['geometry_hash'])
            rt.save(output/'config.json', config)
            rt.save(output/'matrix.json', matrix)
            # Retain actual source bytes, including dirty/new files, not just a Git SHA.
            for name, checksum in identity['source']['files_sha256'].items():
                if checksum != 'missing':
                    destination = output/'source'/name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(rt.REPO/name, destination)
            campaign = dict(schema_version=3, stage='simulation', fingerprint=fingerprint, identity=identity,
                            quantities=quantities, created_unix=time.time(), limitations=rt.LIMITATIONS,
                            status='preflight', coverage='0/26', scientific_validity='unvalidated',
                            job_records={r['id']: dict(status='not_started') for r in matrix['contributions']},
                            snapshots={name: rt.digest(output/name) for name in
                                ('config.json', 'matrix.json', 'quantities.tsv', 'geometry.json')})
            rt.save(path, campaign)
        from study.campaign import validate_snapshots
        validate_snapshots(output, campaign)
        if 'preflight' not in campaign:
            from study.preflight import check
            folder = probe/'decay-preflight'
            check(build, folder)
            campaign['preflight'] = str((folder/'preflight.json').relative_to(output))
            campaign['preflight_artifacts'] = rt.artifacts(folder)
            rt.save(path, campaign)
        from study.campaign import validate_preflight
        try:
            validate_preflight(output, campaign)  # all four gates, regardless of statistics
        except ValueError as error:
            campaign.update(status='preflight_failed', scientific_validity='incomplete; failed environment gate',
                            error=str(error))
            rt.save(path, campaign)
            raise
        try:
            schedule_jobs(output, [r for r in matrix['contributions'] if r['id'] in selected],
                          config, campaign, matrix, tools['simulation'], args.jobs, args.retry_failed)
        finally:
            update_campaign(output, campaign, matrix)
        from study.campaign import validate_campaign
        jobs = validate_campaign(output, allow_partial=True)
        print(f"Campaign coverage {campaign['coverage']}; offline structural validation still required")
        if args.archive:
            from study.archive import package
            print('Archive: '+str(package(output)))
        return 0 if len(jobs) == 26 else 2


def positive_integer(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError('must be a positive integer') from None
    if number < 1:
        raise argparse.ArgumentTypeError('must be a positive integer')
    return number


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, default=rt.REPO/'config/study/samuele.json')
    p.add_argument('--matrix', type=Path, default=rt.REPO/'config/study/thesis-table7.1.json')
    p.add_argument('--build', type=Path, help='Directory containing rdecay01 and geometry_quantities')
    p.add_argument('--output', type=Path, help='Campaign directory outside the checkout')
    p.add_argument('--primaries', type=int, help='Primaries per contribution; default canonical target 10000000')
    p.add_argument('--output-mode', choices=('raw','compact','both'), default='raw',
                   help='Stored representation; changing mode requires a new campaign')
    p.add_argument('--jobs', type=positive_integer, default=1,
                   help='Maximum concurrent contributions (default: 1); each Geant4 process uses one worker')
    p.add_argument('--mode', choices=('smoke', 'production'), help='Optional label/default count; --primaries overrides count')
    p.add_argument('--only', nargs='+', help='Contribution IDs; partial coverage exits 2')
    p.add_argument('--resume', action='store_true', help='Explicit spelling of the default safe resume behavior')
    p.add_argument('--retry-failed', action='store_true', help='Retry failed jobs in new attempt directories')
    p.add_argument('--archive', action='store_true', help='Package a complete 26/26 campaign as OUTPUT.tar.gz')
    p.add_argument('--list', '--dry-run', action='store_true', help='Print matrix macros; no simulation')
    p.add_argument('--macros-dir', type=Path, help='Export macros to a new directory; no simulation')
    return p


def main():
    try:
        return run(parser().parse_args())
    except KeyboardInterrupt:
        print('Interrupted; repeat the same command to resume.', file=sys.stderr)
        return 130
    except (ValueError, RuntimeError, OSError, KeyError) as error:
        print(f'Simulation: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
