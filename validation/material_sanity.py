#!/usr/bin/env python3
"""Source-head sanity comparison from old/new constructed exports; no transport-rate claim."""
import argparse
import csv
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from study.source_matrix import read_matrix, quantity_for, vessel_material_comparison, reference_resistor_mass_kg


def quantities(path):
    with Path(path).open() as f:
        return {r['component']: {k: float(r[k]) if k in ('mass_kg','density_g_cm3','volume_mm3') else
                int(r[k]) if k=='pieces' else r[k] for k in r}
                for r in csv.DictReader((l for l in f if not l.startswith('#')),delimiter='\t')}


def compare(old_path,new_path):
    repo=Path(__file__).resolve().parents[1]
    old,new=quantities(old_path),quantities(new_path)
    v1=read_matrix(repo/'config/study/cygno-300elj-radioassay-v1.json',historical=True)
    v2=read_matrix(repo/'config/study/cygno-300elj-radioassay-v2.json')
    def activities(matrix,q,component):
        return {r['chain_start']['name']:r['activity']*quantity_for(r,q)*1000
                for r in matrix['contributions'] if r['component']==component}
    result={'activity_unit':'mBq per independent source head; not a transported detector-rate ratio',
            'components':new,'reference_resistor_mass_kg':reference_resistor_mass_kg()}
    for c in ('RingSupports','RingStrips','Resistors','Vessel'):
        a,b=activities(v1,old,c),activities(v2,new,c)
        result[c]=dict(old_pieces=old[c]['pieces'],new_pieces=new[c]['pieces'],
                       old_mass_kg=old[c]['mass_kg'],new_mass_kg=new[c]['mass_kg'],
                       old_activity_mBq=a,new_activity_mBq=b,
                       old_sum_mBq=sum(a.values()),new_sum_mBq=sum(b.values()),
                       old_to_new_sum_ratio=sum(a.values())/sum(b.values()))
    r=new['Vessel'];density=r['density_g_cm3']
    comparison=vessel_material_comparison(r['mass_kg'],density,new['RingSupports']['density_g_cm3'])
    assert abs(comparison['volume_cm3']*1000-r['volume_mm3'])<1e-9*r['volume_mm3']
    assert new['RingSupports']['mass_kg']==old['RingSupports']['mass_kg']
    assert new['Resistors']['geometry_material']=='ResistorFusedSilica'
    result['vessel_decision']=comparison
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('old_quantities',type=Path);p.add_argument('new_quantities',type=Path)
    a=p.parse_args();print(json.dumps(compare(a.old_quantities,a.new_quantities),indent=2))
