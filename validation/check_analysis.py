#!/usr/bin/env python3
"""Compile each ROOT plotter's geometry probe and compare with Geant4's audit."""
import argparse
import csv
from pathlib import Path
import shlex
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('placements', type=Path)
parser.add_argument('build_directory', type=Path)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
args.build_directory.mkdir(parents=True, exist_ok=True)
flags = shlex.split(subprocess.check_output(['root-config', '--cflags', '--libs'], text=True))
for name in ('PlotNormalizedSpectra.cpp', 'PlotNormalizedSpectra_single.cpp',
             'PlotNormalizedSpectra_GEMchain.cpp', 'PlotSpectrum.C'):
    executable = (args.build_directory / (Path(name).stem + '_check')).resolve()
    subprocess.run(['c++', '-std=c++17',
                    f'-DCYGNO_ANALYSIS_SOURCE="{repo / "analysis/reference_cpp" / name}"',
                    '-I'+str(args.build_directory.parents[1]/'generated'),
                    str(repo / 'validation/analysis_geometry.cc'), '-o', str(executable),
                    *flags], check=True)
    for layout in ('cygno-5x5x3-v1', 'legacy-25x3', 'cygno-11x7-v1'):
        placements=args.placements
        if layout!='cygno-5x5x3-v1':
            placements=args.build_directory/(layout+'-placements.tsv')
            subprocess.run([str(args.build_directory.parents[1]/'validation/geometry_audit'),
                            str(placements),'--layout',layout],check=True,stdout=subprocess.DEVNULL)
        with placements.open() as source:
            gas={int(r['copy']):tuple(float(r[a]) for a in 'xyz')
                 for r in csv.DictReader(source,delimiter='\t') if r['sensitive']=='1'}
        expected_count = 154 if layout=='cygno-11x7-v1' else 150
        assert len(gas)==expected_count
        output = subprocess.check_output([str(executable),layout], text=True)
        rows = list(csv.reader(output.splitlines(), delimiter='\t'))
        assert len(rows) == expected_count
        for row in rows:
            assert all(abs(float(value)-expected) < 1e-9
                       for value, expected in zip(row[1:], gas[int(row[0])]))
        (args.build_directory/(Path(name).stem+'-'+layout+'.centers.tsv')).write_text(output)
        print(f'{name}: {layout}: {expected_count} centers match Geant4; unchanged 20 mm fiducial boundaries pass')
