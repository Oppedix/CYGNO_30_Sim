"""Portable campaign integrity checks; standard library only, no local build needed."""
import math
from pathlib import Path, PurePosixPath
from study import runtime as rt
from study.source_matrix import require, read_matrix, read_quantities, LAYOUT_MODULE_COUNTS


def inside(root, name):
    path = PurePosixPath(name)
    require(not path.is_absolute() and bool(path.parts) and '..' not in path.parts and '\\' not in name,
            'Unsafe campaign path: '+name)
    result = root.joinpath(*path.parts)
    require(result.resolve().is_relative_to(root.resolve()) and not result.is_symlink(), 'Unsafe campaign link')
    return result


def validate_snapshots(output, campaign):
    identity = campaign['identity']
    require(campaign['fingerprint'] == rt.object_digest(identity), 'Campaign fingerprint mismatch')
    require(set(campaign['snapshots']) == {'config.json', 'matrix.json', 'geometry.json', 'quantities.tsv'},
            'Missing campaign snapshots')
    for name, checksum in campaign['snapshots'].items():
        require(rt.digest(inside(output, name)) == checksum, 'Snapshot checksum mismatch: '+name)
    require(rt.read(output/'config.json') == identity['config'] and rt.read(output/'matrix.json') == identity['matrix'],
            'Configuration/matrix identity mismatch')
    for name, checksum in identity['source']['files_sha256'].items():
        if checksum != 'missing':
            require(rt.digest(inside(output/'source', name)) == checksum, 'Source snapshot mismatch: '+name)
    cfg, env = identity['config'], identity['effective_environment']
    quantities = read_quantities(output/'quantities.tsv', layout=cfg['layout'], model=cfg['model'],
                                 geometry_hash=env['geometry_hash'])
    require(quantities == campaign['quantities'], 'Quantity mismatch')
    require(f"# compiled-source-hash: {env['source_hash']}" in (output/'quantities.tsv').read_text().splitlines(),
            'Quantity source hash mismatch')
    geometry = rt.read(output/'geometry.json')
    require(geometry['layout'] == cfg['layout'] and geometry['geometry_hash'] == env['geometry_hash'] and
            geometry['source_hash'] == env['source_hash'], 'Geometry identity mismatch')
    require(set(geometry['gas_centers_mm']) == {str(i) for i in range(2*LAYOUT_MODULE_COUNTS[cfg['layout']])},
            'Invalid gas copy map')
    for values in [geometry['gas_size_mm'], *geometry['gas_centers_mm'].values()]:
        require(len(values) == 3 and all(math.isfinite(v) for v in values), 'Invalid geometry coordinates')
    require(all(v > 40 for v in geometry['gas_size_mm']), 'Invalid fiducial dimensions')


def validate_preflight(output, campaign):
    path = inside(output, campaign['preflight'])
    rt.check_artifacts(path.parent, {'artifacts': campaign['preflight_artifacts']})
    preflight = rt.read(path)
    names = {'u238-default', 'u238-enabled', 'th232-full', 'bi212-full'}
    require(set(preflight['checks']) == names and preflight['complete'] and
            all(c['status'] == 'passed' and not c['PART122'] for c in preflight['checks'].values()),
            'Four-case decay preflight failed; use a validated environment and a new campaign')
    for name, check in preflight['checks'].items():
        expected = campaign['identity']['effective_environment'].copy()
        if name == 'u238-default':
            expected['radioactive_decay_time_threshold_s'] = check['environment']['radioactive_decay_time_threshold_s']
        require(check['environment'] == expected, 'Preflight environment mismatch')


def validate_job(output, row, campaign):
    config = campaign['identity']['config']
    directory = output/'jobs'/row['id']
    job = rt.read(directory/'manifest.json')
    require(job['contribution'] == row['id'] and job['campaign_fingerprint'] == campaign['fingerprint'],
            'Mixed contribution/campaign identity')
    macro = rt.macro_for(row, config)
    require(job['fingerprint'] == rt.object_digest(dict(campaign=campaign['fingerprint'], contribution=row, macro=macro)),
            'Job fingerprint mismatch')
    require(job['status'] == 'complete', 'Incomplete job')
    attempt = inside(directory, job['attempt'])
    require(rt.read(attempt/'manifest.json') == job, 'Attempt manifest mismatch')
    rt.check_artifacts(attempt, job)
    require((attempt/'run.mac').read_text() == macro and job['macro_sha256'] == rt.digest(attempt/'run.mac'),
            'Macro mismatch')
    require(job['seeds'] == rt.seeds_for(config['seed'], row['id']) and job['workers'] == 1 and
            job['requested_primaries'] == config['primaries_per_job'], 'Job configuration mismatch')
    receipt = rt.read(attempt/'simulation.command.json')
    require(receipt.get('returncode') == 0 and not receipt.get('timed_out') and not receipt.get('interrupted'),
            'Incomplete simulation receipt')
    accounting = rt.validate_simulation_log((attempt/'simulation.log').read_text(errors='replace'),
        campaign['identity']['effective_environment'], config['primaries_per_job'])
    require(job['accounting'] == accounting and job['generated_primaries'] == accounting['GeneratedPrimaries'],
            'Manifest/log accounting mismatch')
    raw = inside(attempt, job['raw_path'])
    require(raw.name in ('raw.root', 'raw_t0.root') and raw.stat().st_size > 0 and
            list((attempt/'outfiles_V2').glob('*.root')) == [raw], 'Invalid raw output')
    return job, raw


def validate_campaign(output, allow_partial=False):
    campaign = rt.read(output/'campaign.json')
    require(campaign['schema_version'] == 2 and campaign['stage'] == 'simulation', 'Not a stage A campaign')
    validate_snapshots(output, campaign)
    validate_preflight(output, campaign)
    matrix = read_matrix(output/'matrix.json')
    jobs = {}
    records = campaign['job_records']
    require(set(records) == {r['id'] for r in matrix['contributions']}, 'Invalid campaign job coverage')
    for row in matrix['contributions']:
        path = output/'jobs'/row['id']/'manifest.json'
        job = rt.read(path) if path.exists() else dict(status='not_started')
        require(job == records[row['id']], 'Campaign/job manifest disagreement')
        if job['status'] == 'complete':
            jobs[row['id']] = validate_job(output, row, campaign)
    require(campaign['coverage'] == f'{len(jobs)}/26' and
            (campaign['status'] == 'complete') == (len(jobs) == 26), 'Campaign completeness mismatch')
    require(allow_partial or len(jobs) == 26, 'Incomplete campaign; use --allow-partial for labeled diagnostics')
    return jobs
