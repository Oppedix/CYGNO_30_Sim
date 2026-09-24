#!/usr/bin/env python3
"""Small optional same-seed transport test, independent of production campaign gates."""
import argparse
from pathlib import Path
import sys
import numpy as np
import uproot
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from study import runtime as rt
from study.source_matrix import read_matrix, require
from analysis.compact.parity import validate
from analysis.compact.benchmark import report
from analysis.common.inputs import canonical_input
from analysis.common.spectra import accumulate, summarize, scale_for


def run(build, output, primaries=30, contribution='GEMsCore_K40'):
    require(1<=primaries<=1000,'Diagnostic limited to 1..1000 primaries')
    output.mkdir(parents=True,exist_ok=False)
    row=next(r for r in read_matrix(rt.REPO/'config/study/thesis-table7.1.json')['contributions'] if r['id']==contribution)
    config=rt.load_config(rt.REPO/'config/study/samuele.json') | dict(primaries_per_job=primaries)
    rt.invoke([build/'geometry_quantities',output/'quantities.tsv',config['layout'],output/'geometry.json'],
              output,'geometry',120)
    geometry=rt.read(output/'geometry.json')
    expected={k:config[k] for k in ('layout','model','source_policy')} | dict(geometry_hash=geometry['geometry_hash'])
    paths={}
    for mode in ('raw','compact','both'):
        folder=output/mode;folder.mkdir()
        (folder/'run.mac').write_text(rt.macro_for(row,config | dict(output_mode=mode)))
        rt.invoke([build/'rdecay01',folder/'run.mac','1','--layout',config['layout'],'--output-mode',mode],
                  folder,'simulation',180)
        files=list((folder/'outfiles_V2').glob('*.root'))
        require(len(files)==1,'Expected single worker output');paths[mode]=files[0]
    with uproot.open(paths['raw']) as raw, uproot.open(paths['both']) as both:
        for tree in ('Hits','RunMetadata','RunAccounting'):
            a,b=raw[tree].arrays(library='np'),both[tree].arrays(library='np')
            require(a.keys()==b.keys(),'Transport schema mismatch')
            for key in a:
                require(np.array_equal(a[key],b[key]),'Output perturbed transport: '+tree+'.'+key)
        parity=validate(both,expected,primaries,geometry,step_size=37)
    results=[]
    for mode in ('raw','compact','both'):
        with uproot.open(paths[mode]) as file:
            _,stream,_=canonical_input(file,expected,primaries,geometry)
            results.append(accumulate(stream,geometry))
    for result in results[1:]:
        require(result[2]==results[0][2] and all(np.array_equal(a,b) for a,b in zip(result[:2],results[0][:2])),
                'Standalone compact spectrum mismatch')
    measurements=report(paths['raw'],paths['compact']) | dict(contribution=contribution,parity=parity,transport_unchanged=True)
    rt.save(output/'compact-validation.json',measurements)
    print(measurements)
    return measurements

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--primaries',type=int,default=30)
    p.add_argument('--contribution',default='GEMsCore_K40')
    a=p.parse_args();run(a.build.resolve(),a.output.resolve(),a.primaries,a.contribution)
