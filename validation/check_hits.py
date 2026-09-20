#!/usr/bin/env python3
"""Check a single run's worker files against the constructed gas geometry.

Requires PyROOT. This validates schema and basic invariants, not a spectrum or
nuclear ancestry. Events without gas steps need not appear in the Hits tree.
"""
import argparse
import csv
import math
from collections import Counter

import ROOT

SCHEMA = [
    ("EventNumber", "Int_t"), ("ParticleName", "Char_t"),
    ("ParticleID", "Int_t"), ("ParticleTag", "Int_t"), ("ParentID", "Int_t"),
    ("x_hits", "Double_t"), ("y_hits", "Double_t"), ("z_hits", "Double_t"),
    ("EnergyDeposit", "Double_t"), ("VolumeNumber", "Int_t"),
    ("Nucleus", "Char_t"), ("ProcessType", "Char_t"),
]


def check(placements, events, paths):
    with open(placements) as source:
        gas = {int(row["copy"]): row for row in csv.DictReader(source, delimiter="\t")
               if row["sensitive"] == "1"}
    assert len(gas) == 150
    seen_events = set()
    total_rows = positive_deposits = radioactive_rows = 0
    for path in paths:
        source = ROOT.TFile.Open(path)
        assert source and not source.IsZombie(), path
        tree = source.Get("Hits")
        assert tree, f"Missing Hits: {path}"
        leaves = list(tree.GetListOfLeaves())
        assert [(l.GetName(), l.GetTypeName()) for l in leaves] == SCHEMA
        assert [b.GetName() for b in tree.GetListOfBranches()] == [n for n, _ in SCHEMA]
        file_events, volumes, nuclei = set(), set(), Counter()
        for index in range(tree.GetEntries()):
            tree.GetEntry(index)
            row = {l.GetName(): l.GetValueString() if kind == "Char_t" else l.GetValue()
                   for l, (_, kind) in zip(leaves, SCHEMA)}
            event, volume = int(row["EventNumber"]), int(row["VolumeNumber"])
            assert 0 <= event < events and volume in gas, (path, index, row)
            assert row["ParticleID"] >= 1 and row["ParentID"] >= 0
            assert row["ParticleTag"] == {"e-": 0, "e+": 1, "gamma": 2, "alpha": 3}.get(row["ParticleName"], -1)
            assert math.isfinite(row["EnergyDeposit"]) and row["EnergyDeposit"] >= 0
            cell = gas[volume]
            for axis in "xyz":
                position = row[axis + "_hits"]
                local = position - float(cell[axis])
                assert math.isfinite(position)
                # Allow Geant4 boundary round-off (1 nm), not misplaced steps.
                assert float(cell[axis+"min"])-1e-6 <= local <= float(cell[axis+"max"])+1e-6, (path, index, row)
            positive_deposits += row["EnergyDeposit"] > 0
            radioactive_rows += row["ProcessType"] == "RadioactiveDecay"
            file_events.add(event)
            volumes.add(volume)
            nuclei[row["Nucleus"]] += 1
        assert not seen_events.intersection(file_events), "One event appears in multiple worker files"
        seen_events.update(file_events)
        total_rows += tree.GetEntries()
        print(f"{path}: {tree.GetEntries()} rows, {len(file_events)} events with hits, "
              f"{len(volumes)} gas IDs, nuclei={dict(nuclei)}")
        source.Close()
    assert total_rows > 0 and positive_deposits > 0 and radioactive_rows > 0
    print(f"PASS: 12 unchanged branches; {total_rows} rows inside their gas cells; "
          f"{positive_deposits} positive deposits, {radioactive_rows} radioactive-decay rows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("placements", help="geometry_audit TSV")
    parser.add_argument("events", type=int, help="number requested by beamOn")
    parser.add_argument("files", nargs="+", help="worker ROOT files from ONE run")
    args = parser.parse_args()
    check(args.placements, args.events, args.files)
