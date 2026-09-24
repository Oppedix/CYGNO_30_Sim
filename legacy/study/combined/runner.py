#!/usr/bin/env python3
"""Legacy combined PyROOT/C++ workflow. New campaigns: study/simulate.py then study/analyze.py."""
import argparse
import json
import os
from pathlib import Path
import platform
import math
import re
import sys
import time

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from study.source_matrix import read_matrix, read_quantities, quantity_for, decay_commands, require, LAYOUTS
from legacy.study.combined.root_io import inspect_raw, inspect_processed, export_spectra

from study.runtime import (REPO, ENV_KEYS, RDM_COMMAND, RDM_SECONDS, LIMITATIONS,
    digest, object_digest, save, read, compiled_source_hash, source_state, load_config,
    validate_counts, seeds_for, macro_for, invoke, parse_environment, dataset_state,
    locked, artifacts, check_artifacts)

TOOLS = {'simulation': 'rdecay01', 'processor': 'analysis/SimpleProcessEvents',
         'plotter': 'analysis/PlotNormalizedSpectra', 'quantities': 'geometry_quantities'}


def normalization(rows, jobs, quantities, identity):
    lines = ['# normalization-format: quantity-v2', f"# layout: {identity['layout']}",
             f"# detector-model: {identity['model']}", f"# source-policy: {identity['source_policy']}",
             '# provenance: Table 7.1; actual construction and generated counts; chain validity and campaign coverage in summary.json']
    for row in rows:
        count = jobs[row['id']]['accounting']['GeneratedPrimaries']
        quantity = quantity_for(row, quantities)
        unit = 'piece' if row['activity_unit'] == 'Bq/piece' else 'kg'
        source = jobs[row['id']]['processed_path']
        # std::quoted understands backslash escaping, not JSON unicode escapes.
        quote = lambda text: '"'+str(text).replace('\\', '\\\\').replace('"', '\\"')+'"'
        lines.append(f'{row["component"]} {row["chain_start"]["name"]} {quantity:.17g} {unit} '
                     f'{row["activity"]:.17g} {row["activity_unit"]} {count} {quote(row["category"])} {quote(source)}')
    return '\n'.join(lines)+'\n'


def run_job(output, row, config, campaign, tools, identity, retry):
    directory = output/'jobs'/row['id']; directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory/'manifest.json'
    fingerprint = object_digest(dict(campaign=campaign['fingerprint'], contribution=row,
                                      macro=macro_for(row, config)))
    previous = read(manifest_path) if manifest_path.exists() else None
    if previous:
        require(previous['fingerprint'] == fingerprint, f'Job identity mismatch: {row["id"]}')
        if previous['status'] == 'complete':
            attempt = directory/previous['attempt']
            check_artifacts(attempt, previous)
            accounting = inspect_raw(attempt/'outfiles_V2/raw_t0.root', identity, config['primaries_per_job'])
            require(accounting == previous['accounting'], 'Accounting changed on resume')
            inspect_processed(attempt/'processed.root', identity)
            print(f"REUSE {row['id']}", flush=True)
            return previous
        if previous['status'] not in ('running', 'interrupted') and not retry:
            print(f"RETAIN {row['id']}: {previous['status']} (use --retry-failed)", flush=True)
            return previous
    attempts = sorted(directory.glob('attempt-*'))
    attempt = directory/f'attempt-{len(attempts)+1:04d}'; attempt.mkdir()
    manifest = dict(fingerprint=fingerprint, contribution=row['id'], status='running',
                    attempt=attempt.name, seeds=seeds_for(config['seed'], row['id']), workers=1,
                    requested_primaries=config['primaries_per_job'], generated_primaries=None, chain_validity='unvalidated',
                    previous_attempt=previous['attempt'] if previous else None)
    save(manifest_path, manifest)
    try:
        (attempt/'run.mac').write_text(macro_for(row, config))
        if config['mode'] == 'production' and th_chain(row) and not campaign.get('th_chain_preflight_passed', False):
            raise RuntimeError('Th/Bi preflight failed: contribution incomplete; use a compatible environment')
        log = invoke([tools['simulation'], attempt/'run.mac', '1', '--layout', config['layout']],
                     attempt, 'simulation', config['timeout_seconds'])
        require(parse_environment(log) == campaign['identity']['effective_environment'], 'Runtime environment changed')
        thresholds = re.findall(r'CYGNO_RUN radioactive_decay_time_threshold_s (\S+)', log)
        require(thresholds and all(math.isclose(float(v), RDM_SECONDS, rel_tol=1e-12) for v in thresholds),
                'Worker did not use the required radioactive-decay threshold')
        roots = list((attempt/'outfiles_V2').glob('*.root'))
        raw = attempt/'outfiles_V2/raw_t0.root'
        require(roots == [raw], 'Expected exactly one single-worker raw file')
        manifest['accounting'] = inspect_raw(raw, identity, config['primaries_per_job'])
        manifest['generated_primaries'] = manifest['accounting']['GeneratedPrimaries']
        processed = attempt/'processed.root'
        invoke([tools['processor'], raw, processed], attempt, 'processing', config['timeout_seconds'])
        manifest['processed_groups'] = inspect_processed(processed, identity)
        manifest['processed_path'] = str(processed)
        if th_chain(row) and not campaign.get('th_chain_preflight_passed', False):
            raise RuntimeError('Th/Bi preflight failed: small successful attempt cannot certify this contribution')
        manifest['status'] = 'complete'
    except KeyboardInterrupt:
        manifest.update(status='interrupted', error='Ctrl-C; retained attempt; same command resumes')
        raise
    except (ValueError, RuntimeError, OSError) as error:
        manifest.update(status='failed', error=str(error), chain_validity='incomplete')
    finally:
        manifest['artifacts'] = artifacts(attempt)
        save(attempt/'manifest.json', manifest)
        save(manifest_path, manifest)
    print(f"{manifest['status'].upper()} {row['id']}" + (': '+manifest['error'] if 'error' in manifest else ''), flush=True)
    return manifest


def th_chain(row):
    return row['chain_start']['name'] in ('Th232', 'Th228') and row['stop_before'] is None


def campaign_job_records(output, matrix):
    """Embed observed attempt state in the campaign; job files remain authoritative."""
    result = {}
    for row in matrix['contributions']:
        path = output/'jobs'/row['id']/'manifest.json'
        if path.exists():
            job = read(path)
            result[row['id']] = {key: job.get(key) for key in
                ('status', 'attempt', 'seeds', 'requested_primaries', 'generated_primaries',
                 'chain_validity', 'error')}
        else:
            result[row['id']] = dict(status='not_started')
    return result


def campaign_preflight(build, output):
    from study.preflight import check
    check(build, output)
    checks = read(output/'preflight.json')['checks']
    require(checks['u238-enabled']['status'] == 'passed', 'Long-lived primary preflight failed')
    return all(checks[name]['status'] == 'passed' for name in ('th232-full', 'bi212-full'))


def run(args):
    config = load_config(args.config)
    if getattr(args, 'mode', None):
        config['mode'] = args.mode
        config['primaries_per_job'] = 2 if args.mode == 'smoke' else 10_000_000
    if getattr(args, 'primaries', None) is not None:
        config['primaries_per_job'] = args.primaries
    validate_counts(config)
    matrix = read_matrix(args.matrix)
    selected = set(args.only or [row['id'] for row in matrix['contributions']])
    require(selected <= {row['id'] for row in matrix['contributions']}, 'Unknown contribution in --only')
    if getattr(args, 'list', False) or getattr(args, 'macros_dir', None):
        rows = [row for row in matrix['contributions'] if row['id'] in selected]
        if getattr(args, 'macros_dir', None):
            folder = args.macros_dir.resolve()
            require(not folder.is_relative_to(REPO), 'Export macros outside the repository')
            folder.mkdir(parents=True, exist_ok=False)
            for row in rows:
                (folder/(row['id']+'.mac')).write_text(macro_for(row, config))
            save(folder/'config.json', config)
        for index, row in enumerate(rows, 1):
            print(f"{index}/{len(rows)} {row['id']} ({row['category']})\n{macro_for(row, config)}")
        return 0
    require(args.build is not None, '--build is required to run or regenerate analysis')
    output = (args.output or Path.home()/'cygno-runs'/('samuele-'+config['mode'])).resolve()
    build = args.build.resolve()
    tools = {key: str(build/value) for key, value in TOOLS.items()}
    require(all(Path(p).is_file() for p in tools.values()), 'Build simulation, analysis and validation targets first')
    with locked(output):
        # Keep every probe; probe failure/mismatch must never overwrite campaign/jobs.
        probes = output/'probes'; probes.mkdir(exist_ok=True)
        probe = probes/f'probe-{time.time_ns()}'; probe.mkdir()
        analysis_only = getattr(args, 'analysis_only', False)
        if analysis_only:
            require((output/'campaign.json').is_file(), 'No existing campaign to analyze')
            environment = read(output/'campaign.json')['identity']['effective_environment']
        else:
            (probe/'environment.mac').write_text(RDM_COMMAND+'\n/control/echo CYGNO_ENVIRONMENT_PROBE\n')
            environment = parse_environment(invoke([tools['simulation'], probe/'environment.mac', '1',
                                                   '--layout', config['layout']], probe, 'environment', config['timeout_seconds']))
        require(math.isclose(float(environment['radioactive_decay_time_threshold_s']), RDM_SECONDS, rel_tol=1e-12),
                'Effective radioactive-decay threshold differs from the study setting')
        require(environment['source_hash'] == compiled_source_hash(), 'Stale build: compiled source fingerprint differs; rebuild')
        require(environment['geometry_hash'] == digest(REPO/'common/DetectorGeometry.hh'), 'Stale geometry build')
        import ROOT
        identity = dict(config=config, matrix=matrix, source=source_state(),
                        build_tools={key: dict(path=value, sha256=digest(value)) for key, value in tools.items()},
                        cmake_cache_sha256=digest(build/'CMakeCache.txt'),
                        effective_environment=environment, datasets=dataset_state(environment),
                        execution_environment={key: value for key, value in sorted(os.environ.items())
                          if key.startswith(('G4', 'GEANT4', 'DYLD_', 'LD_')) or key in ('ROOTSYS', 'OMP_NUM_THREADS')},
                        python=sys.version, python_executable=sys.executable, root=ROOT.gROOT.GetVersion(),
                        platform=platform.platform())
        fingerprint = object_digest(identity)
        campaign_path = output/'campaign.json'
        if campaign_path.exists():
            campaign = read(campaign_path)
            require(campaign['fingerprint'] == fingerprint and campaign['identity'] == identity,
                    'Campaign identity changed (source/build/config/matrix/environment); use a new output directory')
            require(digest(output/'quantities.tsv') == campaign['quantities_sha256'], 'Constructed quantities changed')
        else:
            # Refuse orphan job state instead of attaching it to a new campaign.
            require(not (output/'jobs').exists(), 'Orphan job state without campaign manifest')
            quantity_path = probe/'quantities.tsv'
            invoke([tools['quantities'], quantity_path, config['layout']], probe, 'quantities', config['timeout_seconds'])
            require(f"# compiled-source-hash: {environment['source_hash']}" in quantity_path.read_text().splitlines(),
                    'Stale quantity exporter build')
            (output/'quantities.tsv').write_bytes(quantity_path.read_bytes())
            campaign = dict(schema_version=1, fingerprint=fingerprint, identity=identity,
                            quantities_sha256=digest(output/'quantities.tsv'), limitations=LIMITATIONS,
                            created_unix=time.time(), scientific_validity='unvalidated', status='preflight',
                            matrix_sha256=object_digest(matrix))
            save(campaign_path, campaign)
            save(output/'config.json', config); save(output/'matrix.json', matrix)
        if 'th_chain_preflight_passed' not in campaign:
            require(not analysis_only, 'Campaign preflight is incomplete')
            campaign['th_chain_preflight_passed'] = campaign_preflight(build, probe/'decay-preflight')
            save(campaign_path, campaign)
        expected = {key: config[key] for key in ('layout', 'model', 'source_policy')}
        expected['geometry_hash'] = environment['geometry_hash']
        expected['source_hash'] = environment['source_hash']
        quantities = read_quantities(output/'quantities.tsv', layout=config['layout'], model=config['model'],
                                     geometry_hash=expected['geometry_hash'])
        require(campaign.get('quantities', quantities) == quantities, 'Embedded quantities changed')
        campaign['quantities'] = quantities
        jobs = {}
        campaign['status'] = 'running'
        save(campaign_path, campaign)
        scheduled = 0
        for row in matrix['contributions']:
            if row['id'] in selected:
                scheduled += 1
                print(f"JOB {scheduled}/{len(selected)} ({100*(scheduled-1)/len(selected):.1f}% finished): {row['id']}", flush=True)
                try:
                    if analysis_only:
                        path = output/'jobs'/row['id']/'manifest.json'
                        previous = read(path) if path.exists() else dict(status='not_started')
                        if previous['status'] != 'complete':
                            jobs[row['id']] = previous
                            continue
                    jobs[row['id']] = run_job(output, row, config, campaign, tools, expected,
                                               args.retry_failed and not analysis_only)
                except KeyboardInterrupt:
                    campaign['status'] = 'interrupted'
                    campaign['job_records'] = campaign_job_records(output, matrix)
                    save(campaign_path, campaign)
                    raise
                except (ValueError, RuntimeError, OSError) as error:
                    # Corruption of an existing complete job is not an automatic retry.
                    jobs[row['id']] = dict(status='invalid', error=str(error))
                    print(f"INVALID {row['id']}: {error}", flush=True)
            else:
                jobs[row['id']] = dict(status='not_selected')
        completed = [row for row in matrix['contributions'] if jobs[row['id']]['status'] == 'complete']
        report = dict(campaign_fingerprint=fingerprint, mode=config['mode'], scientific_validity='unvalidated',
                      limitations=LIMITATIONS, jobs={key: value['status'] for key, value in jobs.items()},
                      coverage=f'{len(completed)}/26', complete_matrix=len(completed) == 26)
        reports = output/'reports'; reports.mkdir(exist_ok=True)
        report_dir = reports/f'report-{time.time_ns()}'; report_dir.mkdir()
        save(report_dir/'summary.json', report)
        # Only validated completed selected jobs enter diagnostics. Coverage is
        # explicit; a partial report is never a full-matrix result.
        if completed:
            norm = report_dir/'normalization.tsv'
            norm.write_text(normalization(completed, jobs, quantities, expected))
            try:
                invoke([tools['plotter'], norm], report_dir, 'plotting', config['timeout_seconds'])
                save(report_dir/'spectra.json', export_spectra(report_dir/'NormalizedHisto.root', completed, environment['source_hash']))
                from legacy.study.combined.figures import render
                render(report_dir, read(report_dir/'spectra.json'), report)
                report['analysis_status'] = 'complete'
            except (ValueError, RuntimeError, OSError) as error:
                report.update(analysis_status='failed', analysis_error=str(error))
        else:
            report['analysis_status'] = 'no_completed_jobs'
        save(report_dir/'summary.json', report)
        save(output/'latest-report.json', dict(path=str(report_dir), **report))
        campaign['job_records'] = campaign_job_records(output, matrix)
        campaign['jobs'] = {key: value['status'] for key, value in campaign['job_records'].items()}
        campaign['status'] = 'complete' if all(value == 'complete' for value in campaign['jobs'].values()) else 'incomplete'
        save(campaign_path, campaign)
        for name, status in report['jobs'].items():
            if status not in ('complete', 'not_selected'):
                print(f'INCOMPLETE {name}: {status}', flush=True)
        print(f'Job scheduling finished: {len(selected)}/{len(selected)} (100%); successful {len(completed)}', flush=True)
        print(f"Pipeline coverage {report['coverage']}; chain validity UNVALIDATED; {report_dir}", flush=True)
        return 0 if len(completed) == len(selected) and report['analysis_status'] == 'complete' else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=REPO/'config/study/samuele.json')
    parser.add_argument('--build', type=Path)
    parser.add_argument('--output', type=Path, help='Default: ~/cygno-runs/samuele-MODE')
    parser.add_argument('--mode', choices=('smoke', 'production'))
    parser.add_argument('--primaries', type=int, help='Generated primaries per contribution')
    parser.add_argument('--list', '--dry-run', dest='list', action='store_true', help='Print matrix/macros; no Geant4')
    parser.add_argument('--macros-dir', type=Path, help='Export individual macros to a new directory; no Geant4')
    parser.add_argument('--analysis-only', action='store_true', help='Revalidate completed results and regenerate plots; no Geant4')
    parser.add_argument('--matrix', type=Path, default=REPO/'config/study/thesis-table7.1.json')
    parser.add_argument('--only', nargs='+', help='Explicit diagnostic subset; never called a complete matrix')
    parser.add_argument('--retry-failed', action='store_true', help='New attempts; retain every old artifact')
    args = parser.parse_args()
    try:
        return run(args)
    except KeyboardInterrupt:
        print('Interrupted. Completed jobs are preserved; repeat the same command to resume.', file=sys.stderr)
        return 130
    except (ValueError, RuntimeError, OSError) as error:
        print(f'Study runner: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
