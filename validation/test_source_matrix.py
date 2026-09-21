#!/usr/bin/env python3
"""Table transcription, chain partition, actual quantities and weighted spectra."""
import array
import copy
import hashlib
import math
import subprocess
import sys
import tempfile
from pathlib import Path
import ROOT
ROOT.gROOT.SetBatch(True)
repo=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(repo))
from study.source_matrix import read_matrix, validate_matrix, read_quantities, quantity_for, decay_commands
build=Path(sys.argv[1]).resolve()
root=build/'validation-results';root.mkdir(exist_ok=True)
out=Path(tempfile.mkdtemp(prefix='source-matrix-',dir=root))
fingerprint=hashlib.sha256((repo/'common/DetectorGeometry.hh').read_bytes()).hexdigest()
matrix=read_matrix(repo/'config/study/thesis-table7.1.json')
rows=matrix['contributions']

# Independently transcribed micro-/milli-Bq values from printed Table 7.1.
expected={
 'GEMsCore':([296,56.9,71.2],1e-6), 'GEMsOuter':([.131,.034],1e-6),
 'RingSupports':([296,56.9,71.2],1e-6), 'RingStrips':([.131,.034],1e-6),
 'Cathodes':([.131,.034],1e-6), 'Vessel':([.131,.034],1e-6),
 'Sensors':([2,2.8,9],1e-3), 'Lens':([123,40.7,300],1e-6),
 'Resistors':([1,.14,1.2,.04,.18,.13],1e-6)}
for component,(values,multiplier) in expected.items():
    component_rows=[r for r in rows if r['component']==component]
    names=['U238','Th232','K40','U235','Ra226','Th228'][:len(values)]
    assert [r['chain_start']['name'] for r in component_rows]==names
    for row,value in zip(component_rows,values):
        assert math.isclose(row['activity'],value*multiplier,rel_tol=1e-15)
assert sum(r['activity_unit']=='Bq/piece' for r in rows)==6
assert sum(r['activity_basis']=='upper-limit-used-as-value' for r in rows)==6
for parent,daughter in [('U238','Ra226'),('Th232','Th228')]:
    upstream=next(r for r in rows if r['id']=='Resistors_'+parent)
    downstream=next(r for r in rows if r['id']=='Resistors_'+daughter)
    assert upstream['stop_before']==downstream['chain_start'] and downstream['stop_before'] is None
    commands=decay_commands(upstream)
    assert f"/stopChain/ZStopDecay {downstream['chain_start']['Z']}" in commands
    assert f"/stopChain/AStopDecay {downstream['chain_start']['A']}" in commands
    assert decay_commands(downstream)[-2:]==['/stopChain/ZStopDecay 0','/stopChain/AStopDecay 0']
    assert not any(r['component']!='Resistors' and r['chain_start']['name']==daughter for r in rows)
for row in rows:
    assert '/rdecay01/fullChain true' in decay_commands(row)

def rejects(call):
    try: call()
    except (ValueError,KeyError,TypeError): return
    raise AssertionError('Expected rejection')

for field,value in [('activity_unit','Bq/piece'),('chain_policy','upper-segment'),
                    ('activity_basis','table-value'),('category','wrong'),('activity',float('nan')),
                    ('full_chain',False),('stop_before',{'name':'Ra226','Z':88,'A':226})]:
    bad=copy.deepcopy(matrix);bad['contributions'][0][field]=value
    rejects(lambda:validate_matrix(bad))
for change in ('duplicate','missing','extra_equilibrium'):
    bad=copy.deepcopy(matrix)
    if change=='missing': bad['contributions'].pop()
    else:
        row=copy.deepcopy(rows[0])
        if change=='extra_equilibrium':
            row.update(id='GEMsCore_Ra226',chain_start=dict(name='Ra226',Z=88,A=226),
                       chain_policy='lower-segment',equilibrium_daughters=[])
        bad['contributions'].append(row)
    rejects(lambda:validate_matrix(bad))
bad=copy.deepcopy(matrix)
next(r for r in bad['contributions'] if r['id']=='Resistors_U238')['stop_before']=None
rejects(lambda:validate_matrix(bad))

# Export the actual nine source lists for both profiles, with independently
# expected placement counts and analytic vessel mass (copper at 8.96 g/cm3).
quantities={}
for layout in ('legacy-25x3','cygno-5x5x3-v1'):
    path=out/(layout+'.tsv')
    with (out/(layout+'.log')).open('w') as log:
        subprocess.run([str(build/'validation/geometry_quantities'),str(path),layout],check=True,stdout=log,stderr=subprocess.STDOUT)
    quantities[layout]=read_quantities(path,layout=layout,model='code-compatible',geometry_hash=fingerprint)
    q=quantities[layout]
    counts=dict(Cathodes=75,GEMsOuter=450,GEMsCore=450,RingSupports=150,RingStrips=600,
                Resistors=750,Lens=300,Sensors=300,Vessel=1)
    assert {c:v['pieces'] for c,v in q.items()}==counts
    full=(12616.,2428.,1028.8) if layout=='legacy-25x3' else (2536.,4036.,5599.4)
    expected_vessel=(math.prod(full)-math.prod(x-10 for x in full))*8.96e-6
    # Boolean GetCubicVolume uses Geant4's deterministic Monte Carlo estimator,
    # not exact box subtraction. This is a 5% diagnostic bound, not a replacement
    # for the actual mass. The exporter separately checks exact construction sums.
    discrepancy=q['Vessel']['mass_kg']/expected_vessel-1
    assert abs(discrepancy)<.05,(layout,q['Vessel'],expected_vessel)
    print(layout,'constructed vessel kg=',q['Vessel']['mass_kg'],
          'analytic kg=',expected_vessel,'relative difference=',discrepancy)
    assert math.isclose(q['Resistors']['mass_kg'],750*1.6*.55*3.2*3.97e-6,rel_tol=1e-12)
    for row in rows:
        expected_quantity=750 if row['component']=='Resistors' else q[row['component']]['mass_kg']
        assert quantity_for(row,q)==expected_quantity
    for kwargs in [dict(layout='other'),dict(model='thesis-7.3'),dict(geometry_hash='wrong')]:
        args=dict(layout=layout,model='code-compatible',geometry_hash=fingerprint)|kwargs
        rejects(lambda:read_quantities(path,**args))
assert quantities['legacy-25x3']['Vessel']!=quantities['cygno-5x5x3-v1']['Vessel']
for component in expected.keys()-{'Vessel'}:
    assert quantities['legacy-25x3'][component]==quantities['cygno-5x5x3-v1'][component]

# Two electron groups: one inside the unchanged cut, one outside it. Numerical
# energies/locations are hand-selected; no radioactive transport is involved.
def fixture(layout):
    path=out/(layout+'.root');f=ROOT.TFile(str(path),'RECREATE');t=ROOT.TTree('elabHits','synthetic')
    event=array.array('i',[0]);t.Branch('evNumber',event,'evNumber/I')
    strings={'PartName':ROOT.std.string('e-'),'Nucleus':ROOT.std.string('synthetic')}
    for key,value in strings.items(): t.Branch(key,value)
    vectors={key:ROOT.std.vector('double')() for key in ('EDep_Out','VolNnum_Out','X_Vertex','Y_Vertex','Z_Vertex')}
    for key,value in vectors.items(): t.Branch(key,value)
    for i,x in enumerate((0.,231.)):
        event[0]=i
        for key,value in dict(EDep_Out=.02,VolNnum_Out=37.,X_Vertex=x,Y_Vertex=0.,Z_Vertex=250.25).items():
            vectors[key].clear();vectors[key].push_back(value)
        t.Fill()
    t.Write()
    for key,value in dict(CygnoLayout=layout,CygnoGeometry=fingerprint,CygnoDetectorModel='code-compatible',CygnoSourcePolicy='historical').items():
        ROOT.TNamed(key,value).Write()
    f.Close();return path

plotters=('PlotNormalizedSpectra','PlotNormalizedSpectra_single','PlotNormalizedSpectra_GEMchain')
for layout,q in quantities.items():
    source=fixture(layout)
    config=out/(layout+'-normalization.tsv')
    headers=f'# normalization-format: quantity-v2\n# layout: {layout}\n# detector-model: code-compatible\n# source-policy: historical\n# provenance: synthetic spectra with Table 7.1 and actual constructed quantities; NOT simulated background rates\n'
    lines=[];scales={};categories={}
    for index,row in enumerate(rows):
        component=row['component'];quantity=quantity_for(row,q);unit='piece' if component=='Resistors' else 'kg'
        generated=100+index
        lines.append(f'{component} {row["chain_start"]["name"]} {quantity:.17g} {unit} {row["activity"]:.17g} {row["activity_unit"]} {generated} "{row["category"]}" "{source}"\n')
        scale=row['activity']*quantity*31536000/generated
        scales[row['id']]=scale
        categories[row['category']]=categories.get(row['category'],0.)+scale
    config.write_text(headers+''.join(lines))
    for plotter in plotters:
        directory=out/(layout+'-'+plotter);directory.mkdir()
        with (directory/'plot.log').open('w') as log:
            subprocess.run([str(build/'analysis'/plotter),str(config)],cwd=directory,check=True,stdout=log,stderr=subprocess.STDOUT)
        f=ROOT.TFile.Open(str(directory/'NormalizedHisto.root'))
        assert f.Get('NormalizationConfiguration').GetTitle()==config.read_text()
        for suffix,factor in [('',2),('_cut',1)]:
            assert f.Get('Hstack'+suffix).GetHists().GetSize()==26
            assert f.Get('Categories/Hstack'+suffix).GetHists().GetSize()==7
            for name,scale in scales.items():
                h=f.Get(name+suffix)
                assert math.isclose(h.Integral(),factor*scale,rel_tol=1e-12)
                assert math.isclose(h.GetBinError(h.FindBin(20.)),math.sqrt(factor)*scale,rel_tol=1e-12)
            for category,scale in categories.items():
                h=f.Get('Categories/'+category+suffix)
                assert math.isclose(h.Integral(),factor*scale,rel_tol=1e-12)
                expected_variance=factor*sum(scales[r['id']]**2 for r in rows if r['category']==category)
                assert math.isclose(h.GetBinError(h.FindBin(20.))**2,expected_variance,rel_tol=1e-12)
        f.Close()
    # All unit/quantity errors fail before touching an existing output.
    resistor=f'Resistors U238 750 piece 1e-6 Bq/piece 100 "Resistors" "{source}"\n'
    malformed=[resistor.replace('750 piece','750 kg'), resistor.replace('750 piece','750.5 piece'),
               resistor.replace('Bq/piece','uBq/piece'), resistor.replace('100 "','100.5 "'),
               resistor.replace('750 piece','0 piece'), resistor.replace('1e-6','-1e-6'),
               resistor+resistor, resistor+resistor.replace('U238','K40').replace('750 piece','751 piece')]
    for index,text in enumerate(malformed):
        bad=out/'bad.tsv';bad.write_text(headers+text)
        for plotter in plotters:
            sentinel=out/'NormalizedHisto.root';sentinel.write_bytes(b'keep')
            result=subprocess.run([str(build/'analysis'/plotter),str(bad)],cwd=out,capture_output=True,text=True)
            assert result.returncode!=0,(index,plotter)
            assert sentinel.read_bytes()==b'keep'
print('PASS: all 26 assays/chain starts, split/reset controls, both constructed quantity sets, per-piece normalization, weighted category sums/errors and invalid-unit rejection;',out)
