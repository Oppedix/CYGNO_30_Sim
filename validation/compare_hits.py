#!/usr/bin/env python3
"""Compare Hits schema and every row exactly, ignoring ROOT file metadata.

Requires PyROOT. Pass two isolated outfiles_V2 directories from identical
single-worker, fixed-seed runs; this does not reorder or aggregate the steps.
"""

import sys
from pathlib import Path

import ROOT


def read_hits(path):
    source = ROOT.TFile.Open(str(path))
    if not source or source.IsZombie():
        raise ValueError(f"Cannot read {path}")
    try:
        tree = source.Get("Hits")
        if not tree:
            raise ValueError(f"Missing Hits tree in {path}")
        schema = [
            (branch.GetName(), [(leaf.GetName(), leaf.GetTypeName())
                               for leaf in branch.GetListOfLeaves()])
            for branch in tree.GetListOfBranches()
        ]
        leaves = list(tree.GetListOfLeaves())
        rows = []
        for entry in range(tree.GetEntries()):
            tree.GetEntry(entry)
            rows.append(tuple(
                leaf.GetValueString() if leaf.GetTypeName() == "Char_t"
                else leaf.GetValue() for leaf in leaves
            ))
        return schema, rows
    finally:
        source.Close()


def main(before, after):
    before_files = {p.name: p for p in Path(before).glob("*.root")}
    after_files = {p.name: p for p in Path(after).glob("*.root")}
    if not before_files or before_files.keys() != after_files.keys():
        raise ValueError("Missing or different ROOT filenames; use isolated run directories")
    total_rows = 0
    for name in sorted(before_files):
        schema_before, rows_before = read_hits(before_files[name])
        schema_after, rows_after = read_hits(after_files[name])
        if schema_before != schema_after:
            raise ValueError(f"Schema differs: {name}")
        if len(rows_before) != len(rows_after):
            raise ValueError(f"Row count differs: {name}")
        for index, (old, new) in enumerate(zip(rows_before, rows_after)):
            if old != new:
                raise ValueError(f"Row {index} differs: {name}\n{old}\n{new}")
        total_rows += len(rows_before)
        print(f"{name}: {len(schema_before)} branches, {len(rows_before)} identical rows")
    if total_rows == 0:
        raise ValueError("No hit rows: this run does not exercise sensitive-detector output")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: compare_hits.py BEFORE_OUTPUT_DIRECTORY AFTER_OUTPUT_DIRECTORY")
    main(*sys.argv[1:])
