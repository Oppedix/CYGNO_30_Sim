#!/usr/bin/env python3
"""Stage B: validate and analyze a raw/compact/both campaign using uproot, without CERN ROOT."""
import argparse
import importlib.metadata
from pathlib import Path
import sys
import tempfile
import tarfile

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from study import runtime as rt
from study.source_matrix import require, read_matrix
from study.campaign import validate_campaign
from study.archive import open_campaign


def analysis_source_state():
    """An archived source snapshot is executable without installing Git."""
    if (rt.REPO/'.git').exists():
        return rt.source_state()
    paths = sorted((rt.REPO/'study').glob('*.py')) + sorted((rt.REPO/'analysis').rglob('*.py'))
    requirements = rt.REPO/'study/requirements-analysis.txt'
    if requirements.exists():
        paths.append(requirements)
    return dict(revision=None, status='source snapshot without Git metadata',
                files_sha256={str(p.relative_to(rt.REPO)): rt.digest(p) for p in paths})


def analyze(root, output, allow_partial=False, step_size='64 MB'):
    import uproot
    from analysis.common.inputs import canonical_input
    from analysis.common.spectra import accumulate, scale_for, summarize
    from analysis.common.reporting import render
    output = output.resolve()
    require(not output.exists(), 'Analysis output must be a new directory; previous results are never overwritten')
    require(not output.is_relative_to(root.resolve()), 'Analysis output must be outside the campaign')
    jobs = validate_campaign(root, allow_partial=allow_partial)
    require(jobs, 'No complete jobs to analyze')
    campaign = rt.read(root/'campaign.json')
    config = campaign['identity']['config']
    env = campaign['identity']['effective_environment']
    expected = {key: config[key] for key in ('layout', 'model', 'source_policy')}
    expected['geometry_hash'] = env['geometry_hash']
    geometry = rt.read(root/'geometry.json')
    matrix = read_matrix(root/'matrix.json')
    results, inputs, raw_reference = [], {}, []
    for row in matrix['contributions']:
        if row['id'] not in jobs:
            continue
        job, data_path = jobs[row['id']]
        checksum = rt.digest(data_path)
        reference = []
        with uproot.open(data_path, array_cache=None) as file:
            accounting, stream, provenance = canonical_input(file, expected, job['requested_primaries'],
                geometry, step_size, job.get('output_mode','raw'), job.get('output_schema_version',0), reference.append)
            require(accounting == job['accounting'], 'ROOT/manifest accounting mismatch')
            counts, histogram, processed = accumulate(stream, geometry)
            inputs[row['id']] = dict(path=str(data_path.relative_to(root)), sha256=checksum,
                accounting=accounting, processed_groups=processed, **provenance)
        require(rt.digest(data_path) == checksum, 'Data file changed during analysis')
        scale = scale_for(row, campaign['quantities'], accounting['GeneratedPrimaries'])
        results.append((row, scale, counts, histogram))
        if reference:
            raw_reference.append((row, scale, reference[0][0], reference[0][1]))
        print(f"Validated and processed {row['id']}: {processed} groups", flush=True)
    complete = len(jobs) == 26
    summary = dict(schema_version=1, stage='analysis', campaign_fingerprint=campaign['fingerprint'],
        campaign_identity=campaign['identity'], mode=config['mode'], coverage=f'{len(jobs)}/26',
        complete_matrix=complete, scientific_validity=(
            'software-complete; environment-preflight-passed; physical-model-and-rate-validation-pending' if complete
            else 'incomplete; partial diagnostic sums only'),
        limitations=campaign['limitations']+[
            'Nucleus is the most recently tracked ion label, not guaranteed per-hit ancestry.',
            'Historical grouping and first-position fiducialization retained; group Poisson errors are not primary-level errors.',
            'Published tables are reference comparisons only; geometry/source limitations are unchanged.'],
        inputs=inputs, python=sys.version, analysis_source=analysis_source_state(),
        packages={name: importlib.metadata.version(name) for name in ('uproot','awkward','numpy','matplotlib')},
        step_size=step_size, processing_version='event-boundaries-and-eof-v2')
    spectra = summarize(results)
    if raw_reference:
        require(len(raw_reference)==len(results), 'Mixed both-mode parity coverage')
        require(summarize(raw_reference)==spectra, 'Normalized raw/compact campaign mismatch')
        summary['normalized_parity'] = dict(status='passed', comparison='exact',
            checks=['contribution counts/rates/variances', 'category sums/densities/flows',
                    'Table 7.2 total inputs', 'Table 7.3 category inputs'])
    output.parent.mkdir(parents=True, exist_ok=True)
    # Publish only a fully written report; failures never leave plausible final output.
    with tempfile.TemporaryDirectory(prefix='.cygno-analysis-', dir=output.parent) as directory:
        staged = Path(directory)/'report'
        staged.mkdir()
        rt.save(staged/'spectra.json', spectra)
        rt.save(staged/'campaign.json', campaign)
        render(staged, spectra, summary)
        summary['output_sha256'] = rt.artifacts(staged)
        rt.save(staged/'analysis-manifest.json', summary)
        require(not output.exists(), 'Analysis output appeared during processing')
        staged.rename(output)
    print(f"Analysis coverage {summary['coverage']}; {output}")
    return 0 if complete else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Campaign directory or .tar.gz archive')
    parser.add_argument('--output', type=Path, required=True, help='New report directory')
    parser.add_argument('--allow-partial', action='store_true', help='Produce explicitly partial diagnostics; exits 2')
    parser.add_argument('--step-size', default='64 MB', help='uproot memory budget per chunk (default: 64 MB)')
    args = parser.parse_args()
    try:
        with open_campaign(args.input) as root:
            return analyze(root, args.output, args.allow_partial, args.step_size)
    except (ValueError, RuntimeError, OSError, KeyError, ImportError, tarfile.TarError) as error:
        print(f'Analysis: {error}', file=sys.stderr)
        return 1

if __name__ == '__main__': sys.exit(main())
