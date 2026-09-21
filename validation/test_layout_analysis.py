#!/usr/bin/env python3
"""Layout/model identity gates and off-center fiducial fixtures; no transport."""
import array
import hashlib
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import ROOT
from check_hits import SCHEMA
ROOT.gROOT.SetBatch(True)
build=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
out=Path(tempfile.mkdtemp(prefix='layout-analysis-',dir=build/'validation-results'))
current='cygno-5x5x3-v1'; legacy='legacy-25x3'
fingerprint=hashlib.sha256((repo/'common/DetectorGeometry.hh').read_bytes()).hexdigest()
baseline='d0e9f189266be3f0a608bba332b4fe5e5f17d9c7c2c6ef4bd95f53408f73c039'
processor=build/'analysis/SimpleProcessEvents'
plotters=[build/'analysis'/n for n in ('PlotNormalizedSpectra','PlotNormalizedSpectra_single','PlotNormalizedSpectra_GEMchain')]

def run(args, ok=True, cwd=out):
    result=subprocess.run([str(a) for a in args],cwd=cwd,capture_output=True,text=True)
    assert (result.returncode==0)==ok,(args,result.stdout,result.stderr)
    return result

def metadata(path, layout, model='code-compatible', policy='historical', hash_value=fingerprint,
             rows=1, omit=()):
    f=ROOT.TFile(str(path),'UPDATE');tree=ROOT.TTree('RunMetadata','Run identity');fields={}
    for name,value in dict(Layout=layout,DetectorModel=model,SourcePolicy=policy,GeometryHash=hash_value).items():
        if name in omit: continue
        fields[name]=array.array('b',value.encode()+bytes(256-len(value)))
        tree.Branch(name,fields[name],name+'/C')
    for _ in range(rows): tree.Fill()
    tree.Write('',ROOT.TObject.kOverwrite);f.Close()

def markers(path, layout=current, hash_value=fingerprint, model=None, policy=None):
    f=ROOT.TFile(str(path),'UPDATE')
    data=dict(CygnoLayout=layout,CygnoGeometry=hash_value)
    if model is not None: data['CygnoDetectorModel']=model
    if policy is not None: data['CygnoSourcePolicy']=policy
    for k,v in data.items(): ROOT.TNamed(k,v).Write('',ROOT.TObject.kOverwrite)
    f.Close()

def raw(name,layout):
    path=out/(name+'.root');f=ROOT.TFile(str(path),'RECREATE');tree=ROOT.TTree('Hits','Hits');fields={}
    for key,kind in SCHEMA:
        fields[key]=array.array('b',[0]*256) if kind=='Char_t' else array.array('i' if kind=='Int_t' else 'd',[0])
        tree.Branch(key,fields[key],key+'/'+{'Char_t':'C','Int_t':'I','Double_t':'D'}[kind])
    # Independent module-0 centers, not the shared origin/module 37.
    center=(-6048.,-804.,250.25) if layout==legacy else (-1008.,-1608.,-2285.30+250.25)
    for event,offset in enumerate((0.,230.,231.)):
        values=dict(EventNumber=event,ParticleName='e-',ParticleID=1,ParticleTag=0,ParentID=0,
                    x_hits=center[0]+offset,y_hits=center[1],z_hits=center[2],EnergyDeposit=.02,
                    VolumeNumber=0,Nucleus='Synthetic',ProcessType='RadioactiveDecay')
        for key,value in values.items():
            if isinstance(value,str): fields[key][:]=array.array('b',value.encode()+bytes(256-len(value)))
            else: fields[key][0]=value
        tree.Fill()
    tree.Write();f.Close();return path

def identity(path,layout):
    f=ROOT.TFile.Open(str(path))
    for key,value in dict(CygnoLayout=layout,CygnoDetectorModel='code-compatible',CygnoSourcePolicy='historical').items():
        assert f.Get(key).GetTitle()==value,(path,key)
    f.Close()

def config(path,layout,inputs,model='code-compatible',policy='historical'):
    path.write_text(f'# provenance: synthetic unit-scale layout fixture\n# layout: {layout}\n# detector-model: {model}\n# source-policy: {policy}\n'+
                    ''.join(f'{c} X 1 1 31536000 "{p}"\n' for c,p in inputs))
    return path

processed={}
for layout in (current,legacy):
    source=raw(layout,layout);metadata(source,layout)
    destination=out/('elab_'+layout+'.root')
    run([processor,source,destination]);identity(destination,layout);processed[layout]=destination
    f=ROOT.TFile.Open(str(destination));assert f.Get('RunMetadata').GetEntries()==1;f.Close()
    study=config(out/'study.tsv',layout,[('A',destination)])
    for plotter in plotters:
        run([plotter,study]);identity(out/'NormalizedHisto.root',layout)
        f=ROOT.TFile.Open(str(out/'NormalizedHisto.root'))
        assert f.Get('A_X').Integral()==3 and f.Get('A_X_cut').Integral()==2
        f.Close()
    # Explicit assumptions are checked against metadata, never used to override it.
    run([processor,source,out/'match.root','--assume-layout',layout,'--assume-model','code-compatible'])
    for flags in (['--assume-layout',legacy if layout==current else current],
                  ['--assume-model','thesis-7.3']):
        sentinel=out/'reject.root';sentinel.write_bytes(b'preserve-existing-output')
        run([processor,source,sentinel,*flags],ok=False)
        assert sentinel.read_bytes()==b'preserve-existing-output'

# Metadata-free old raw files require BOTH independently verified assumptions.
unversioned=raw('unversioned',legacy)
for flags in ([],['--assume-layout',legacy],['--assume-model','code-compatible']):
    run([processor,unversioned,out/'absent.root',*flags],ok=False)
    assert not (out/'absent.root').exists()
run([processor,unversioned,out/'assumed.root','--assume-layout',legacy,'--assume-model','code-compatible'])
identity(out/'assumed.root',legacy)
# Alias remains available, but also requires a model for unknown data.
run([processor,unversioned,out/'alias.root','--assume-geometry',legacy,'--assume-model','code-compatible'])
for flags in (['--assume-layout','typo'],['--assume-layout',legacy,'--assume-layout',legacy],
              ['--assume-model'],['--unknown'],['--assume-model','thesis-7.3']):
    run([processor,unversioned,out/'bad-option.root',*flags],ok=False)

for case,kw in [('layout',dict(layout='unknown')),('model',dict(model='thesis-7.3')),
                ('policy',dict(policy='uniform-bulk')),('hash',dict(hash_value='wrong')),
                ('rows',dict(rows=2)),('zero',dict(rows=0)),('partial',dict(omit=('DetectorModel',))),
                ('hash_only',dict(omit=('Layout','DetectorModel','SourcePolicy')))]:
    bad=raw('bad_'+case,current);metadata(bad,**(dict(layout=current)|kw))
    run([processor,bad,out/'bad-output.root','--assume-layout',current,'--assume-model','code-compatible'],ok=False)
    assert not (out/'bad-output.root').exists()

# Compatibility is deliberately narrow: known old current markers only.
old=raw('old_markers',current);markers(old,hash_value=baseline)
run([processor,old,out/'old_processed.root']);identity(out/'old_processed.root',current)
f=ROOT.TFile.Open(str(out/'old_processed.root'));assert f.Get('CygnoGeometry').GetTitle()==baseline;f.Close()
markers(old,layout=legacy,hash_value=baseline)
run([processor,old,out/'bad-output.root','--assume-layout',legacy,'--assume-model','code-compatible'],ok=False)
markers(old,hash_value='unknown')
run([processor,old,out/'bad-output.root'],ok=False)
# Phase-1 processed current files carry the current header hash and two markers.
markers(old);run([processor,old,out/'phase1_processed.root'])
markers(old,model='code-compatible') # partial new format is not an old record
run([processor,old,out/'bad-output.root'],ok=False)
# Conflicting raw/processed markers must be rejected, even with explicit assumptions.
conflict=out/'conflict.root';shutil.copyfile(processed[current],conflict)
markers(conflict,layout=legacy,model='code-compatible',policy='historical')
run([processor,conflict,out/'bad-output.root','--assume-layout',legacy,'--assume-model','code-compatible'],ok=False)

# Every normalized plotter preflights ALL files before replacing its output.
for label,layout,inputs,kwargs in [
    ('mixed',current,[('A',processed[current]),('B',processed[legacy])],{}),
    ('wrong_layout',legacy,[('A',processed[current])],{}),
    ('wrong_model',current,[('A',processed[current])],dict(model='thesis-7.3')),
    ('wrong_policy',current,[('A',processed[current])],dict(policy='uniform-bulk')),
    ('unmarked',current,[('A',unversioned)],{}),
    ('conflicting_markers',legacy,[('A',conflict)],{})]:
    study=config(out/(label+'.tsv'),layout,inputs,**kwargs)
    for plotter in plotters:
        sentinel=out/'NormalizedHisto.root';sentinel.write_bytes(b'preserve-existing-spectrum')
        run([plotter,study],ok=False);assert sentinel.read_bytes()==b'preserve-existing-spectrum'
# ROOT macro is also compiled/executed, with positive and mismatch cases.
probe=out/'macro.cc';executable=out/'macro'
probe.write_text('#include "TROOT.h"\n#include "'+str(repo/'analysis/PlotSpectrum.C')+'"\n'
                 'int main(int argc,char**argv) {gROOT->SetBatch(true);try {PlotSpectra(argv[1],argc>2?argv[2]:"",argc>3?argv[3]:"");return 0;}catch(const std::exception& e){std::cerr<<e.what();return 1;}}\n')
flags=shlex.split(subprocess.check_output(['root-config','--cflags','--libs'],text=True))
run(['c++','-std=c++17','-I'+str(build/'generated'),probe,'-o',executable,*flags])
for layout,path in processed.items():
    run([executable,path]);result=out/('histo_'+path.name);identity(result,layout)
    f=ROOT.TFile.Open(str(result));assert f.Get('betaplot').Integral()==3 and f.Get('betaplot_cut').Integral()==2;f.Close()
    before=result.read_bytes()
    run([executable,path,legacy if layout==current else current],ok=False)
    run([executable,path,layout,'thesis-7.3'],ok=False)
    assert result.read_bytes()==before
for path in (unversioned,conflict): run([executable,path],ok=False)
print('PASS: both layouts, metadata, assumptions, compatibility, all plotter cuts and pre-output mismatch gates;',out)
