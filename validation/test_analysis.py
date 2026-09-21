#!/usr/bin/env python3
"""Hand-calculable ROOT fixtures exercise actual processing and plotting binaries."""
import array
import math
import subprocess
import sys
import tempfile
from pathlib import Path
import ROOT
from check_hits import SCHEMA
ROOT.gROOT.SetBatch(True)
build=Path(sys.argv[1]).resolve();root=build/'validation-results';root.mkdir(exist_ok=True)
out=Path(tempfile.mkdtemp(prefix='analysis-',dir=root))

def fixture(name, rows):
    path=out/(name+'.root'); f=ROOT.TFile(str(path),'RECREATE'); t=ROOT.TTree('Hits','Hits'); fields={}
    for key,kind in SCHEMA:
        fields[key]=array.array('b',[0]*256) if kind=='Char_t' else array.array('i' if kind=='Int_t' else 'd',[0])
        t.Branch(key,fields[key],key+'/'+{'Char_t':'C','Int_t':'I','Double_t':'D'}[kind])
    for row in rows:
        data=dict(EventNumber=0,ParticleName='e-',ParticleID=1,ParticleTag=0,ParentID=0,x_hits=0.,y_hits=0.,z_hits=250.25,EnergyDeposit=.001,VolumeNumber=37,Nucleus='Po212',ProcessType='RadioactiveDecay')
        data.update(row)
        for k,v in data.items():
            if isinstance(v,str):
                fields[k][:]=array.array('b',v.encode()+bytes(256-len(v)))
            else: fields[k][0]=v
        t.Fill()
    t.Write();f.Close();return path

def process(name,rows,expected):
    raw=fixture(name,rows); processed=out/('elab_'+name+'.root')
    subprocess.run([str(build/'analysis/SimpleProcessEvents'),str(raw),str(processed),'--assume-layout','cygno-5x5x3-v1','--assume-model','code-compatible'],check=True)
    f=ROOT.TFile.Open(str(processed));t=f.Get('elabHits'); got=[]
    for e in t: got.append((int(e.evNumber),list(e.VolNnum_Out),list(e.EDep_Out)))
    assert len(got)==len(expected),(name,got,expected)
    for actual,want in zip(got,expected):
        assert actual[:2]==want[:2],(name,got)
        assert all(math.isclose(a,b,rel_tol=1e-14) for a,b in zip(actual[2],want[2]))
        assert len(actual[2])==len(want[2])
    f.Close();return processed

process('empty',[],[])
process('one',[{}],[(0,[37.],[.001])])
process('ignored',[dict(ParticleName='gamma')],[])
process('volume_order',[dict(VolumeNumber=38),{},dict(VolumeNumber=38)],[(0,[38.,37.],[.002,.001])])
process('event_boundary',[{},dict(EventNumber=1,ProcessType='eIoni',EnergyDeposit=.002)],[(0,[37.],[.001]),(1,[37.],[.002])])
process('ignored_boundary',[{},dict(EventNumber=1,ParticleName='gamma'),dict(EventNumber=1,ProcessType='ionIoni')],[(0,[37.],[.001]),(1,[37.],[.001])])
process('process_boundary',[{},dict(ProcessType='eIoni'),dict(ProcessType='phot')],[(0,[37.],[.002]),(0,[37.],[.001])])
process('long_label',[dict(Nucleus='Pb208[2614.522000000000000000000]')],[(0,[37.],[.001])])
# Two equal nonzero spectra and two equal empty spectra must all survive sorting,
# including their individual keys and cut stack entries. Keep original bins/cuts.
nonempty=process('spectrum',[dict(EnergyDeposit=.02)],[(0,[37.],[.02])])
empty=out/'elab_empty.root'
configuration=out/'study.tsv';configuration.write_text('# layout: cygno-5x5x3-v1\n# detector-model: code-compatible\n# source-policy: historical\n# provenance: synthetic regression, unit scale; no scientific normalization claim\n'+''.join(f'{c} X 1 1 31536000 "{path}"\n' for c,path in [('A',nonempty),('B',nonempty),('C',empty),('D',empty)]))
for name,bins in [('PlotNormalizedSpectra',900),('PlotNormalizedSpectra_single',1200),('PlotNormalizedSpectra_GEMchain',1200)]:
    directory=out/name;directory.mkdir()
    subprocess.run([str(build/'analysis'/name),str(configuration)],cwd=directory,check=True,stdout=subprocess.DEVNULL)
    f=ROOT.TFile.Open(str(directory/'NormalizedHisto.root'))
    for key in ('Hstack','Hstack_cut'):
        stack=f.Get(key);assert stack.GetHists().GetSize()==4,(name,key)
        assert math.isclose(sum(h.Integral() for h in stack.GetHists()),2.)
    for c in 'ABCD':
        for suffix in ('','_cut'):
            h=f.Get(c+'_X'+suffix); assert h and h.GetNbinsX()==bins
            assert h.Integral()==(1 if c in 'AB' else 0)
    f.Close()
# No accidental overwrite on unversioned input and no automatic historical mass.
assert subprocess.run([str(build/'analysis/SimpleProcessEvents'),str(out/'one.root'),str(out/'rejected.root')],stderr=subprocess.DEVNULL).returncode!=0
historical=Path(__file__).resolve().parents[1]/'config/normalization/PlotNormalizedSpectra.historical.tsv'
assert subprocess.run([str(build/'analysis/PlotNormalizedSpectra'),str(historical)],cwd=out,stderr=subprocess.DEVNULL).returncode!=0
print('PASS: EOF, event/process boundaries, volume order, empty trees, long labels, equal-integral stacks and normalization guard;',out)
# Audit the exported historical tables against the original compiled constants.
# This checks transcription only, never scientific provenance.
import csv, shlex
flags=shlex.split(subprocess.check_output(['root-config','--cflags','--libs'],text=True))
repo=Path(__file__).resolve().parents[1]
for name in ('PlotNormalizedSpectra','PlotNormalizedSpectra_single','PlotNormalizedSpectra_GEMchain'):
    probe=out/(name+'_constants.cc');exe=out/(name+'_constants')
    # The quarantined main is not executed; explicitly bind its old no-argument
    # geometry call in this constants-only probe, without editing the reference.
    probe.write_text('#include <iomanip>\n#include "DetectorGeometry.hh"\nvoid BuildDetectorMap(std::map<Int_t,TVector3>& centers){BuildDetectorMap(centers,cygno::geometry::LayoutId::Current5x5x3);}\n#define main historical_main\n#include "'+str(repo/'legacy/analysis/05a2b92'/f'{name}.cpp')+'"\n#undef main\nint main(){std::cout<<std::setprecision(17);for(const auto& c:ElementMass)for(const auto& a:Contaminant[c.first])std::cout<<c.first<<" "<<a.first<<" "<<c.second<<" "<<a.second<<" "<<NEvents[c.first][a.first]<<"\\n";}\n')
    subprocess.run(['c++','-std=c++17','-I'+str(repo/'analysis'),str(probe),'-o',str(exe),*flags],check=True,stderr=subprocess.DEVNULL)
    expected={tuple(x[:2]):tuple(map(float,x[2:])) for line in subprocess.check_output([str(exe)],text=True).splitlines() if (x:=line.split())}
    actual={tuple(x[:2]):tuple(map(float,x[2:5])) for line in (repo/'config/normalization'/f'{name}.historical.tsv').read_text().splitlines() if not line.startswith('#') and (x:=line.split())}
    assert actual==expected,(name,actual,expected)
print('PASS: all historical normalization values exactly match original compiled tables')
