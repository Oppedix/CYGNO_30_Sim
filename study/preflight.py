#!/usr/bin/env python3
"""Small decay-environment checks, never a background-rate measurement."""
import argparse
import math
from pathlib import Path
import re
import sys
import time

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from study.runner import invoke, parse_environment, save, REPO, RDM_COMMAND, RDM_SECONDS
from study.source_matrix import require



def check(build, output, long_lived_only=False):
    output = output.resolve()
    require(not output.is_relative_to(REPO), 'Preflight outputs must be outside the repository')
    output.mkdir(parents=True, exist_ok=False)
    cases = [('u238-default', 92, 238, 2, False, (90, 234)),
             ('u238-enabled', 92, 238, 2, True, (90, 234))]
    if not long_lived_only:
        cases += [('th232-full', 90, 232, 40, True, (0, 0)),
                  ('bi212-full', 83, 212, 40, True, (0, 0))]
    results = {}
    for name, z, a, count, enabled, stop in cases:
        folder = output/name; folder.mkdir()
        macro = '\n'.join(['/run/verbose 0', '/event/verbose 0', '/tracking/verbose 0',
            '/random/setSeeds 12345 67890', '/output/OutFile preflight',
            *([RDM_COMMAND] if enabled else []), '/detector/RadElement Cathodes',
            f'/isotope/AtomicNumber {z}', f'/isotope/MassNumber {a}',
            '/rdecay01/fullChain true', f'/stopChain/ZStopDecay {stop[0]}',
            f'/stopChain/AStopDecay {stop[1]}', f'/run/beamOn {count}', ''])
        (folder/'run.mac').write_text(macro)
        result = dict(requested_primaries=count, status='failed')
        try:
            log = invoke([build.resolve()/'rdecay01', folder/'run.mac', '1', '--layout', 'legacy-25x3'],
                         folder, 'simulation', 120)
            environment = parse_environment(log)
            result['environment'] = environment
            if enabled:
                require(math.isclose(float(environment['radioactive_decay_time_threshold_s']),
                                     RDM_SECONDS, rel_tol=1e-12), 'Incorrect effective RDM threshold')
            # The printed particle inventory counts transported tracks, even if
            # daughters leave no gas Hits. Do not use nonzero energy as a proxy.
            daughter = bool(re.search(r'\bTh234\s*:', log))
            result['th234_daughter_observed'] = daughter
            if name == 'u238-enabled':
                require(daughter, 'U238 produced no transported Th234 daughter')
            if name == 'u238-default' and math.isclose(float(environment['radioactive_decay_time_threshold_s']), 31536000):
                require(not daughter, 'Unexpected daughter under the one-year default')
            if name in ('th232-full', 'bi212-full'):
                require(bool(re.search(r'\bBi212\s*:', log)) and bool(re.search(r'\bPb208\s*:', log)),
                        'Full-chain preflight did not transport Bi212 and terminal Pb208')
            result['status'] = 'passed'
        except (ValueError, RuntimeError, OSError) as error:
            result['error'] = str(error)
        log = (folder/'simulation.log').read_text(errors='replace') if (folder/'simulation.log').exists() else ''
        result['PART122'] = 'PART122' in log
        result['log'] = str(folder/'simulation.log')
        results[name] = result
        save(output/'preflight.json', dict(created_unix=time.time(), checks=results,
             complete=all(r['status'] == 'passed' for r in results.values()),
             scope='environment preflight; not a rate/branching validation'))
        print(f"{name}: {result['status']}" + (' (PART122)' if result['PART122'] else ''), flush=True)
    return 0 if all(r['status'] == 'passed' for r in results.values()) else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New directory, retained on failure')
    parser.add_argument('--long-lived-only', action='store_true')
    args = parser.parse_args()
    return check(args.build, args.output, args.long_lived_only)


if __name__ == '__main__':
    sys.exit(main())
