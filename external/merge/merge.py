#!/usr/bin/env python3
"""Validate immutable external campaigns and publish a logical statistical join."""
import argparse
import hashlib
import re
from pathlib import Path
import sys
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from study import runtime as rt
from study.source_matrix import require
from external.study.simulate import check_campaign


def build_files(files):
    return {n: h for n, h in files.items() if n in
            ('CMakeLists.txt', 'analysis/CMakeLists.txt', 'validation/CMakeLists.txt') or
            any(n.startswith(d+'/') and Path(n).suffix in suffixes for d, suffixes in
                {'app': {'.cc'}, 'src': {'.cc'}, 'include': {'.hh'},
                 'common': {'.hh', '.in'}, 'analysis': {'.cpp', '.cc', '.hh'}}.items())}


def compatibility(c, root):
    identity = c['identity']; files = identity['source']['files_sha256']
    compiled = build_files(files)
    require(all(n in compiled for n in ('app/rdecay01.cc', 'common/DetectorGeometry.hh',
            'common/ExternalGeometry.hh', 'src/source/PrimaryGeneratorAction.cc', 'CMakeLists.txt')),
            'Missing transport source provenance; compatibility cannot be established')
    require(all(h != 'missing' for h in compiled.values()), 'Missing build source snapshot')
    observed = hashlib.sha256(''.join(f'{n}:{h}\n' for n, h in sorted(compiled.items())).encode()).hexdigest()
    env = identity['environment']
    require(observed == env['source_hash'], 'Unverified compiled source identity')
    require(re.fullmatch('[0-9a-f]{64}', identity.get('executable_sha256', '')), 'Missing/invalid executable identity')
    require(set(identity['datasets']) == set(rt.ENV_KEYS), 'Missing dataset identity')
    datasets = {k: {n: v for n, v in d.items() if n in ('content_sha256', 'files')} for k, d in identity['datasets'].items()}
    require(all(re.fullmatch('[0-9a-f]{64}', d.get('content_sha256', '')) and type(d.get('files')) is int and d['files'] > 0 for d in datasets.values()), 'Unverified datasets')
    cfg = {k: v for k, v in identity['config'].items() if k not in ('seed', 'primaries', 'timeout_seconds', 'id')}
    require(cfg['output_mode'] in ('compact', 'both'), 'Join requires compact external campaigns')
    return dict(config=cfg, environment={k: v for k, v in env.items() if k not in (*rt.ENV_KEYS, 'source_hash')},
                transport_sources={n: h for n, h in compiled.items() if not n.startswith('analysis/')},
                datasets=datasets, geometry={k: v for k, v in rt.read(root/'geometry.json').items() if k != 'source_hash'},
                radius_mm=identity['source_radius_mm'], external_geometry_hash=identity['external_geometry_hash'],
                incident_rate_s=c['incident_rate_s'])


def inventory(root):
    result = {}
    for p in sorted(root.rglob('*')):
        require(not p.is_symlink(), 'Symlinks are not immutable campaign inputs: '+str(p))
        if p.is_file() and p.name != '.runner.lock': result[str(p.relative_to(root))] = rt.digest(p)
    return result


def describe(inputs, *, full=True):
    paths = [p.resolve(strict=True) for p in inputs]
    require(len(paths) >= 2 and len(set(paths)) == len(paths), 'Need at least two distinct campaigns; duplicated input')
    members, seeds, streams, roots, hashes = [], set(), set(), set(), set()
    baseline = None; total = 0
    for path in paths:
        before = inventory(path)
        c, data = check_campaign(path); cfg = c['identity']['config']
        require(c['accounting']['GeneratedPrimaries'] == cfg['primaries'], 'Incorrect generated-primary count')
        for attempt in sorted(path.glob('attempt-*')):
            require(attempt.is_dir() and re.fullmatch(r'attempt-[0-9]+', attempt.name), 'Invalid attempt directory')
            previous = rt.read(attempt/'manifest.json')
            require(previous['attempt'] == attempt.name and previous['fingerprint'] == c['fingerprint'] and
                    previous['identity'] == c['identity'] and previous['status'] in ('complete', 'failed', 'interrupted'),
                    'Unfinished or mismatched historical attempt')
            rt.check_artifacts(attempt, previous)
        signature = compatibility(c, path)
        if baseline is None: baseline = signature
        require(signature == baseline, 'Incompatible physics, geometry, source, build inputs or data environment: '+str(path))
        seed = cfg['seed']; pair = rt.seeds_for(seed, cfg['id'])
        require(len(set(pair)) == 2 and seed not in seeds and not (set(pair) & streams), 'Duplicate seed or overlapping random stream')
        seeds.add(seed); streams.update(pair)
        inode = (data.stat().st_dev, data.stat().st_ino); digest = before[str(data.relative_to(path))]
        require(inode not in roots and digest not in hashes, 'Duplicate ROOT data file')
        roots.add(inode); hashes.add(digest)
        if full:
            import uproot
            from external.analysis.io import groups
            with uproot.open(data, array_cache=None) as f:
                for _ in groups(f, c): pass
        require(before == inventory(path), 'Input changed during validation: '+str(path))
        total += cfg['primaries']
        require(total <= 2**53-1, 'Total exceeds exact ROOT JSON/double integer range')
        members.append(dict(path=str(path), campaign=c, files_sha256=before,
                            root_path=str(data), seed=seed, random_seeds=pair))
    for a in members:
        for b in members:
            ia, ib = a['campaign']['identity'], b['campaign']['identity']
            if ia['executable_sha256'] == ib['executable_sha256']:
                require(ia['environment']['source_hash'] == ib['environment']['source_hash'],
                        'Same executable claims different compiled source identities')
            else:
                build_a = ia['source'].get('worker_build')
                build_b = ib['source'].get('worker_build')
                require(ia['environment']['source_hash'] != ib['environment']['source_hash'] and
                        isinstance(build_a, dict) and set(build_a) == {'machine', 'geant4_config_sha256', 'libraries', 'compiler', 'flags'} and
                        build_a == build_b and bool(build_a['compiler']) and bool(build_a['machine']) and
                        re.fullmatch('[0-9a-f]{64}', build_a['geant4_config_sha256']) and
                        any(n.startswith('libG4') for n in build_a['libraries']) and
                        all(re.fullmatch('[0-9a-f]{64}', h) for h in build_a['libraries'].values()),
                        'Different executable: compiler/ABI compatibility is unverified (analysis-only Git changes alone are harmless)')
    body = dict(external_join_version=1, status='complete', generated_primaries=total,
                compatibility=baseline, members=members,
                normalization='sum integer primary-event counts; scale=incident_rate_s*31536000/sum generated; variance=count*scale^2')
    return body | dict(fingerprint=rt.object_digest(body))


def verify(output, *, full=False):
    saved = rt.read(output/'campaign.json')
    require(saved.get('external_join_version') == 1, 'Not an external logical join')
    require(describe([Path(m['path']) for m in saved['members']], full=full) == saved,
            'Joined campaign or immutable input changed; recreate in a new output directory')
    return saved


def merge(output, inputs):
    output = output.resolve()
    require(not output.exists() and not output.with_name(output.name+'.partial').exists(), 'Output already exists')
    for p in inputs:
        source = p.resolve()
        require(not output.is_relative_to(source) and not source.is_relative_to(output), 'Output must be separate from inputs')
    record = describe(inputs)
    staging = output.with_name(output.name+'.partial'); staging.mkdir(parents=True, exist_ok=False)
    rt.save(staging/'campaign.json', record)
    staging.rename(output)
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--inputs', type=Path, nargs='+')
    p.add_argument('--verify', action='store_true'); p.add_argument('--full', action='store_true')
    a = p.parse_args()
    try:
        require(a.verify != bool(a.inputs), 'Specify --inputs to join, or --verify')
        c = verify(a.output, full=a.full) if a.verify else merge(a.output, a.inputs)
        print(f"Validated external join: {len(c['members'])} campaigns, {c['generated_primaries']} generated primaries")
        return 0
    except (ValueError, RuntimeError, OSError, KeyError, ImportError) as e:
        print('External join: '+str(e), file=sys.stderr); return 1
if __name__ == '__main__': sys.exit(main())
