"""Storage diagnostics for separately generated same-seed raw/compact files."""
import argparse
import json
from pathlib import Path
import uproot
from analysis.raw.io import HITS_SCHEMA, LEGACY_HITS_SCHEMA
from analysis.common.io import output_metadata, tree


def report(raw_path, compact_path):
    with uproot.open(raw_path) as raw, uproot.open(compact_path) as compact:
        raw_format=output_metadata(raw)
        compact_format=output_metadata(compact)
        if raw_format['OutputFormat']!='raw' or compact_format['OutputFormat']!='compact':
            raise ValueError('Benchmark requires standalone raw and compact outputs')
        hits=tree(raw,'Hits',HITS_SCHEMA if raw_format['OutputSchemaVersion'] else LEGACY_HITS_SCHEMA)
        generated=int(raw['RunAccounting']['GeneratedPrimaries'].array(library='np')[0])
        if generated!=int(compact['RunAccounting']['GeneratedPrimaries'].array(library='np')[0]):
            raise ValueError('Benchmark primary counts differ')
        raw_bytes,compact_bytes=Path(raw_path).stat().st_size,Path(compact_path).stat().st_size
        return dict(primaries=generated,raw_hit_rows=int(hits.num_entries),
            canonical_groups=int(compact['Groups'].num_entries),
            group_volume_records=int(compact['GroupVolumes'].num_entries),
            track_records=int(compact['Tracks'].num_entries),
            track_group_records=int(compact['TrackGroups'].num_entries),
            raw_file_bytes=raw_bytes,compact_file_bytes=compact_bytes,
            compression_ratio=raw_bytes/compact_bytes, reduction_fraction=1-compact_bytes/raw_bytes)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw',type=Path,required=True);p.add_argument('--compact',type=Path,required=True)
    args=p.parse_args();print(json.dumps(report(args.raw,args.compact),indent=2))
