"""Exact same-transport parity. No tolerances: ordered additions must be identical."""
from collections import deque
from itertools import zip_longest
import numpy as np
from analysis.raw.io import header as raw_header, hit_chunks
from analysis.raw.preprocess import groups as raw_groups
from analysis.compact.io import header as compact_header
from analysis.compact.preprocess import groups as compact_groups
from analysis.common.spectra import accumulate, group_energy, fiducial, window_flags, histogram_bin
from study.source_matrix import require


def validate(file, expected, requested, geometry, step_size='64 MB', reference_sink=None):
    accounting, hits = raw_header(file, expected, requested)
    compact_accounting, trees = compact_header(file, expected, requested)
    require(accounting==compact_accounting, 'Parity accounting mismatch')
    queues = [deque(),deque()]
    track_count = 0
    def sink(side):
        def accept(record):
            nonlocal track_count
            queues[side].append(record)
            while all(queues):
                require(queues[0].popleft()==queues[1].popleft(), 'Raw/compact track provenance mismatch')
                track_count += 1
        return accept
    def raw(track_sink=None):
        return raw_groups(hit_chunks(hits,requested,expected['layout'],step_size),track_sink)
    raw_stream = raw(sink(0))
    compact_stream = compact_groups(trees,requested,expected['layout'],step_size,sink(1))
    def verified():
        for index,(a,b) in enumerate(zip_longest(raw_stream,compact_stream)):
            require(a is not None and b is not None, 'Raw/compact group count mismatch')
            require(a==b and list(a.volumes)==list(b.volumes), f'Raw/compact group mismatch at {index}')
            for g in (a,b):
                require(g.volumes, 'Empty canonical group')
            def decision(g):
                e=group_energy(g)
                return e, fiducial(g,geometry), window_flags(e), histogram_bin(e)
            require(decision(a)==decision(b), f'Raw/compact analysis decision mismatch at {index}')
            yield b
        require(not any(queues), 'Raw/compact track count mismatch')
    compact_result=accumulate(verified(),geometry)
    raw_result=accumulate(raw(),geometry)
    require(raw_result[2]==compact_result[2] and
            all(np.array_equal(a,b) for a,b in zip(raw_result[:2],compact_result[:2])),
            'Raw/compact spectrum/window mismatch')
    if reference_sink is not None:
        reference_sink(raw_result)
    return dict(status='passed', comparison='exact', processing_version='event-boundaries-and-eof-v2',
                groups=compact_result[2], tracks=track_count,
                group_volumes=int(trees['GroupVolumes'].num_entries),
                checks=['group identities/order/labels/counts','volume order/energy/first position/first time',
                        'track provenance/membership','group energy/fiducial/window flags',
                        'all 900 bins/underflow/overflow/exact counts'])


def main():
    import argparse
    import json
    import uproot
    from pathlib import Path
    from analysis.common.io import tree
    from study.runtime import ACCOUNTING_FIELDS
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True,help='One same-transport both ROOT file')
    p.add_argument('--geometry',type=Path,required=True,help='Matching compiled geometry.json')
    args=p.parse_args()
    geometry=json.loads(args.geometry.read_text())
    expected=dict(layout=geometry['layout'],geometry_hash=geometry['geometry_hash'],
                  model='code-compatible',source_policy='historical')
    with uproot.open(args.input,array_cache=None) as file:
        requested=int(tree(file,'RunAccounting',dict.fromkeys(ACCOUNTING_FIELDS,'int32'),one=True)
                      ['RequestedEvents'].array(library='np')[0])
        print(json.dumps(validate(file,expected,requested,geometry),indent=2))

if __name__=='__main__': main()
