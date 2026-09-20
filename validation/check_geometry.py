#!/usr/bin/env python3
"""Check a 5x5x3 audit against a saved 25x3 audit (standard library only).

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


def check(before_path, after_path):
    before, after = read(before_path), read(after_path)
    assert len(before) == len(after) == 3227
    assert len({r['name'] for r in after}) == len(after), 'Duplicate physical names'
    assert collections.Counter(r['logical'] for r in before) == collections.Counter(r['logical'] for r in after)
    old_modules = [r for r in before if r['logical']=='Cathode']
    new_modules = {r['copy']:r for r in after if r['logical']=='Cathode'}
    assert len(old_modules) == len(new_modules) == 75
    # Baseline nearest cathode is unambiguous in XY; its modules had no Z layers.
    old_patterns=collections.defaultdict(collections.Counter)
    for row in before:
        if row['logical'] in ('World','Vessel'): continue
        cathode=min(old_modules,key=lambda m:(row['x']-m['x'])**2+(row['y']-m['y'])**2)
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
    for module_id,cathode in new_modules.items():
        ix,iy,iz=module_id//15,(module_id//3)%5,module_id%3
        expected=((ix-2)*504,(iy-2)*804,(iz-1)*2285.3)
        assert all(math.isclose(cathode[a],expected[i],abs_tol=1e-9) for i,a in enumerate('xyz'))
        envelopes[module_id]=[[math.inf]*3,[-math.inf]*3]
    for row in after:
        if row['logical']=='World': continue
        lo=[row[a]+row[a+'min'] for a in 'xyz']
        hi=[row[a]+row[a+'max'] for a in 'xyz']
        assert all(world[a+'min'] < lo[i] and hi[i] < world[a+'max'] for i,a in enumerate('xyz')), row['name']
        if row['logical']=='Vessel': continue
        module_id=row['copy']%75
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
        if row['sensitive']=='1':
            assert row['logical']=='GasVolume'
            gas.add(row['copy'])
            side=row['copy']//75
            assert math.isclose(row['z']-center[2],250.25 if side==0 else -250.25,abs_tol=1e-9)
    assert gas == set(range(150))
    for module_id,pattern in patterns.items():
        assert pattern == reference, (module_id, pattern-reference, reference-pattern)
    for a,b in itertools.combinations(envelopes,2):
        lo1,hi1=envelopes[a]; lo2,hi2=envelopes[b]
        assert any(hi1[i] < lo2[i] or hi2[i] < lo1[i] for i in range(3)), (a,b)
    lo,hi=envelopes[37]
    print('75 modules, 150 gas volumes, 3,227 unique placements: PASS')
    print('All 43 local placements per module, solid descriptions and material assignments match baseline.')
    print('Module envelope [mm]:',lo,hi)
    print('No inter-module envelope intersections, vessel crossings or world protrusions.')
    # Densities and elemental fractions are independently captured by snapshot.
    def materials(path):
        return [l for l in path.read_text().splitlines() if l.startswith(('material ','element '))]
    assert materials(Path(before_path).with_name('geometry.txt')) == materials(Path(after_path).with_name('geometry.txt'))
    print('All material densities, compositions, temperatures and pressures match baseline.')


if __name__=='__main__':
    if len(sys.argv)!=3: sys.exit('Usage: check_geometry.py BEFORE.tsv AFTER.tsv')
    check(*sys.argv[1:])
