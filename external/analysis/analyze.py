#!/usr/bin/env python3
"""External primary-event spectra from raw, compact or both; no activity/mass scaling."""
import argparse
from itertools import groupby
import math
from pathlib import Path
import re
import sys
if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from external.analysis.io import groups
from external.study.simulate import check_campaign
from study import runtime as rt
from study.source_matrix import require

CHANNELS=('total','electromagnetic','charged_hadron','other')


def channel(particle):
    if particle in ('e-','e+'):return 1
    if particle in ('proton','deuteron','triton','alpha','He3') or re.fullmatch(r'[A-Z][a-z]?[0-9]+(?:\[.*\])?',particle):return 2
    return 3


def spectra(stream):
    # 1000 1-keV bins, with explicit underflow and overflow. Count each primary once per channel.
    counts={name:[0]*1002 for name in CHANNELS}
    windows={name:dict(positive=0,gt10_le400=0) for name in CHANNELS}
    for _,event in groupby(stream,lambda g:g.event):
        energy=[0.]*4
        for group in event:
            for v in group.volumes.values():
                require(math.isfinite(v.energy) and v.energy>=0,'Invalid deposit')
                value=v.energy*1000
                energy[0]+=value;energy[channel(group.particle)]+=value
        for name,value in zip(CHANNELS,energy):
            require(math.isfinite(value),'Event energy overflow')
            if value<=0:continue
            counts[name][min(1001,1+int(value))]+=1
            windows[name]['positive']+=1
            windows[name]['gt10_le400']+=int(10<value<=400)
    return counts,windows


def analyze(source,output):
    import uproot
    source,output=source.resolve(),output.resolve()
    require(not output.is_relative_to(source),'Analysis output must be outside campaign')
    require(not output.exists(),'Analysis output already exists')
    campaign,data=check_campaign(source)
    with uproot.open(data,array_cache=None) as file:
        counts,windows=spectra(groups(file,campaign))
    generated=campaign['accounting']['GeneratedPrimaries']
    scale=campaign['incident_rate_s']*31536000/generated
    staging=output.with_name(output.name+'.partial');staging.mkdir(parents=True,exist_ok=False)
    report=dict(campaign_fingerprint=campaign['fingerprint'],config=campaign['identity']['config'],
                generated_primaries=generated,incident_rate_s=campaign['incident_rate_s'],scale_per_year=scale,
                bins_keV=[0,1000,1000],counts=counts,windows=windows,
                annual_windows={c:{w:n*scale for w,n in ws.items()} for c,ws in windows.items()},
                variance='Poisson primary-event counts times scale squared; flux/model systematics excluded')
    rt.save(staging/'spectra.json',report)
    with (staging/'spectra.tsv').open('w') as f:
        f.write('channel\tbin\tMC_events\tannual_events\tannual_variance\n')
        for name in CHANNELS:
            for index,count in enumerate(counts[name]):
                f.write(f'{name}\t{index}\t{count}\t{count*scale:.17g}\t{count*scale*scale:.17g}\n')
    staging.rename(output)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    try:analyze(a.input,a.output);return 0
    except (ValueError,RuntimeError,OSError,KeyError) as e:
        print('External analysis: '+str(e),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
