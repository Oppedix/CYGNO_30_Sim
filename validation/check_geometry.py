#!/usr/bin/env python3
"""Check any supported layout audit against a saved module reference (standard library only).

Validates every module's local component geometry/material signature, layout,
IDs, names, sensitivity, world/vessel clearance and absence of inter-module
bounding-box intersections. Does not suppress or repair internal overlaps.
"""
import collections
import csv
import itertools
import math
import sys
from pathlib import Path


def read(path):
    with open(path) as source:
        rows = list(csv.DictReader(source, delimiter='\t'))
    for r in rows:
        for key in ('x','y','z','xmin','ymin','zmin','xmax','ymax','zmax'):
            r[key] = float(r[key])
        r['copy'] = int(r['copy'])
    return rows


def local_signature(row, center):
    return (row['logical'], row['material'], row['shape'], row['sensitive'],
            *(round(row[axis]-center[i], 9) for i,axis in enumerate('xyz')))


def check(before_path, after_path, same_layout=False, profile='cygno-5x5x3-v1'):
    assert profile in ('cygno-5x5x3-v1', 'legacy-25x3', 'cygno-11x7-v1'), profile
    before, after = read(before_path), read(after_path)
    count = 77 if profile=='cygno-11x7-v1' else 75
    assert len(after) == count*43+2
    assert len({r['name'] for r in after}) == len(after), 'Duplicate physical names'
    old_modules = [r for r in before if r['logical']=='Cathode']
    new_modules = {r['copy']:r for r in after if r['logical']=='Cathode'}
    old_count=len(old_modules)
    assert len(before)==old_count*43+2
    assert len(new_modules)==count
    # Baseline nearest cathode is unambiguous in XY; its modules had no Z layers.
    old_patterns=collections.defaultdict(collections.Counter)
    for row in before:
        if row['logical'] in ('World','Vessel'): continue
        cathode=(next(m for m in old_modules if m['copy']==row['copy']%old_count) if same_layout
                 else min(old_modules,key=lambda m:(row['x']-m['x'])**2+(row['y']-m['y'])**2))
        center=tuple(cathode[a] for a in 'xyz')
        old_patterns[center][local_signature(row,center)]+=1
    reference=next(iter(old_patterns.values()))
    assert sum(reference.values()) == 43
    assert all(pattern == reference for pattern in old_patterns.values())
    patterns=collections.defaultdict(collections.Counter)
    gas=set()
    envelopes={}
    world=next(r for r in after if r['logical']=='World')
    vessel=next(r for r in after if r['logical']=='Vessel')
    assert set(new_modules) == set(range(count))
    if profile == 'legacy-25x3':
        # Reference transcribed from Samuele 26ddbdb's placement loops, independent
        # of the C++ profile factory. All legacy cathodes share one Z plane.
        with (Path(__file__).parent/'references/legacy-25x3-centers.tsv').open() as f:
            reference_centers = list(csv.DictReader(f, delimiter='\t'))
        assert len(reference_centers) == 75
        expected_centers = {int(r['module_id']): tuple(float(r[a]) for a in 'xyz') for r in reference_centers}
        expected_vessel, expected_world = (6308,1214,514.4), (7000,1714,1640.65)
    elif profile == 'cygno-11x7-v1':
        expected_centers = {m: ((m//7-5)*504, (m%7-3)*804, 0) for m in range(77)}
        expected_vessel, expected_world = (2780,2822,514.4), (7000,3322,1640.65)
    else:
        expected_centers = {m: ((m//15-2)*504, ((m//3)%5-2)*804, (m%3-1)*2285.3) for m in range(75)}
        expected_vessel, expected_world = (1268,2018,2799.7), (7000,2518,3925.95)
    for i,axis in enumerate('xyz'):
        assert math.isclose(vessel[axis+'max'], expected_vessel[i], abs_tol=1e-9)
        assert math.isclose(vessel[axis+'min'], -expected_vessel[i], abs_tol=1e-9)
        assert math.isclose(world[axis+'max'], expected_world[i], abs_tol=1e-9)
        assert math.isclose(world[axis+'min'], -expected_world[i], abs_tol=1e-9)
    for module_id,cathode in new_modules.items():
        expected=expected_centers[module_id]
        assert all(math.isclose(cathode[a],expected[i],abs_tol=1e-9) for i,a in enumerate('xyz'))
        envelopes[module_id]=[[math.inf]*3,[-math.inf]*3]
    for row in after:
        if row['logical']=='World': continue
        lo=[row[a]+row[a+'min'] for a in 'xyz']
        hi=[row[a]+row[a+'max'] for a in 'xyz']
        assert all(world[a+'min'] < lo[i] and hi[i] < world[a+'max'] for i,a in enumerate('xyz')), row['name']
        if row['logical']=='Vessel': continue
        module_id=row['copy']%count
        center=tuple(new_modules[module_id][a] for a in 'xyz')
        patterns[module_id][local_signature(row,center)]+=1
        for i in range(3):
            envelopes[module_id][0][i]=min(envelopes[module_id][0][i],lo[i])
            envelopes[module_id][1][i]=max(envelopes[module_id][1][i],hi[i])
        # A component must be wholly inside the cavity or wholly outside the
        # vessel outer box. Thus no component crosses the common copper shell.
        inside=all(lo[i] > vessel[a+'min']+5 and hi[i] < vessel[a+'max']-5 for i,a in enumerate('xyz'))
        outside=any(hi[i] < vessel[a+'min'] or lo[i] > vessel[a+'max'] for i,a in enumerate('xyz'))
        assert inside or outside, ('Vessel intersection',row['name'])
        if row['logical'] not in ('Lens','Sensor'):
            assert inside, ('Drift/GEM/cage component outside vessel', row['name'])
        if row['sensitive']=='1':
            assert row['logical']=='GasVolume'
            assert row['copy'] not in gas, 'Duplicate gas copy'
            gas.add(row['copy'])
            assert all(math.isclose(row[a],center[i],abs_tol=1e-9) for i,a in enumerate('xy'))
            side=row['copy']//count
            assert math.isclose(row['z']-center[2],250.25 if side==0 else -250.25,abs_tol=1e-9)
    assert gas == set(range(2*count))
    for module_id,pattern in patterns.items():
        assert pattern == reference, (module_id, pattern-reference, reference-pattern)
    for a,b in itertools.combinations(envelopes,2):
        lo1,hi1=envelopes[a]; lo2,hi2=envelopes[b]
        assert any(hi1[i] < lo2[i] or hi2[i] < lo1[i] for i in range(3)), (a,b)
    assert len({tuple(r[a] for a in 'xyz') for r in new_modules.values()})==count
    if profile == 'cygno-11x7-v1':
        occupied = ([min(e[0][i] for e in envelopes.values()) for i in range(3)],
                    [max(e[1][i] for e in envelopes.values()) for i in range(3)])
        for actual, expected in zip(occupied, ((-2770.145,-2812.1275,-1140.650),(2770.075,2812.660,1140.650))):
            assert all(math.isclose(a,b,abs_tol=1e-9) for a,b in zip(actual,expected))
    center_id=next(m for m,r in new_modules.items() if all(r[a]==0 for a in 'xyz'))
    lo,hi=envelopes[center_id]
    print(f'{count} modules, {2*count} gas volumes, {len(after):,} unique placements: PASS')
    print('All 43 local placements per module, solid descriptions and material assignments match baseline.')
    print('Module envelope [mm]:',lo,hi)
    print('No inter-module envelope intersections, vessel crossings or world protrusions.')
    # Densities and elemental fractions are independently captured by snapshot.
    def materials(path):
        return [l for l in path.read_text().splitlines() if l.startswith(('material ','element '))]
    assert materials(Path(before_path).with_name('geometry.txt')) == materials(Path(after_path).with_name('geometry.txt'))
    print('All material densities, compositions, temperatures and pressures match baseline.')


if __name__=='__main__':
    if len(sys.argv) not in (3,4): sys.exit('Usage: check_geometry.py BEFORE.tsv AFTER.tsv [--same-layout]')
    check(*sys.argv[1:3], same_layout=len(sys.argv)==4 and sys.argv[3]=='--same-layout')
