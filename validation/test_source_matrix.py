#!/usr/bin/env python3
"""Layer assays, retained table, chain partition, quantities and weighted spectra."""
import array
import csv
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
matrix=read_matrix(repo/'config/study/cygno-300elj-radioassay-v2.json')
rows=matrix['contributions']

# Independent paper conversion and retained micro-/milli-Bq Table 7.1 values.
expected={
 'GEMsPolyimide':([5.58*12.4,6.82*4.06,108*30.5],1e-6),
 'GEMsCopper':([12*12.4,12*4.06,130*30.5],1e-6),
 'CathodesPolyimide':([5.58*12.4,6.82*4.06,108*30.5],1e-6),
 'CathodesCopper':([12*12.4,12*4.06,130*30.5],1e-6),
 'RingSupports':([9.05,5.05,71.2],1e-6), 'RingStrips':([.131,.034],1e-6),
 'Vessel':([.131,.034],1e-6),
 'Sensors':([2,2.8,9],1e-3), 'Lens':([123,40.7,300],1e-6),
 'Resistors':([4.30*12.4,2.00*4.06,7.90*30.5],math.pi*(3**2-2**2)*17*2.20e-12)}
for component,(values,multiplier) in expected.items():
    component_rows=[r for r in rows if r['component']==component]
    names=['U238','Th232','K40','U235','Ra226','Th228'][:len(values)]
    assert [r['chain_start']['name'] for r in component_rows]==names
    for row,value in zip(component_rows,values):
        assert math.isclose(row['activity'],value*multiplier,rel_tol=1e-15)
assert sum(r['activity_unit']=='Bq/piece' for r in rows)==3
assert sum(r['activity_basis']=='conservative-old-K-proxy' for r in rows)==1
for parent,daughter in [('U238','Ra226'),('Th232','Th228')]:
    resistor=next(r for r in rows if r['id']=='Resistors_'+parent)
    assert resistor['stop_before'] is None and resistor['chain_policy']=='equilibrium'
    assert resistor['equilibrium_daughters']==[daughter]
    assert decay_commands(resistor)[-2:]==['/stopChain/ZStopDecay 0','/stopChain/AStopDecay 0']
    assert not any(r['component']=='Resistors' and r['chain_start']['name'] in ('U235','Ra226','Th228') for r in rows)
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
            row.update(id='GEMsPolyimide_Ra226',chain_start=dict(name='Ra226',Z=88,A=226),
                       chain_policy='lower-segment',equilibrium_daughters=[])
        bad['contributions'].append(row)
    rejects(lambda:validate_matrix(bad))
bad=copy.deepcopy(matrix)
next(r for r in bad['contributions'] if r['id']=='Resistors_U238')['stop_before']=dict(name='Ra226',Z=88,A=226)
rejects(lambda:validate_matrix(bad))

# Export the actual ten source lists for all profiles, with independently
# expected placement counts and analytic vessel mass (copper at 8.96 g/cm3).
quantities={}
for layout in ('legacy-25x3','cygno-5x5x3-v1','cygno-11x7-v1'):
    path=out/(layout+'.tsv')
    with (out/(layout+'.log')).open('w') as log:
        subprocess.run([str(build/'geometry_quantities'),str(path),layout],check=True,stdout=log,stderr=subprocess.STDOUT)
    quantities[layout]=read_quantities(path,layout=layout,model='cygno-300elj-v2',geometry_hash=fingerprint)
    q=quantities[layout]
    counts=dict(CathodesPolyimide=75,CathodesCopper=150,GEMsCopper=900,GEMsPolyimide=450,RingSupports=150,RingStrips=3750,
                Resistors=3900,Lens=300,Sensors=300,Vessel=1)
    if layout=='cygno-11x7-v1':
        counts=dict(CathodesPolyimide=77,CathodesCopper=154,GEMsCopper=924,GEMsPolyimide=462,RingSupports=154,RingStrips=3850,
                    Resistors=4004,Lens=308,Sensors=308,Vessel=1)
    assert {c:v['pieces'] for c,v in q.items()}==counts
    materials=dict(CathodesPolyimide='G4_KAPTON',CathodesCopper='G4_Cu',GEMsPolyimide='G4_KAPTON',
                   GEMsCopper='G4_Cu',RingSupports='PMMA',RingStrips='G4_Cu',Resistors='ResistorFusedSilica',
                   Lens='Silicon Dioxide',Sensors='G4_Si',Vessel='G4_Cu')
    assert {c:v['geometry_material'] for c,v in q.items()}==materials
    with path.open() as f:
        exported={r['component']:r for r in csv.DictReader((l for l in f if not l.startswith('#')),delimiter='\t')}
    for c,v in exported.items():
        assert math.isclose(float(v['volume_mm3'])*float(v['density_g_cm3'])*1e-6,q[c]['mass_kg'],rel_tol=1e-12)
    assert math.isclose(float(exported['Resistors']['density_g_cm3']),2.20,rel_tol=1e-12)
    assert math.isclose(float(exported['RingSupports']['density_g_cm3']),1.190,rel_tol=1e-12)
    assert math.isclose(float(exported['Lens']['density_g_cm3']),2.65,rel_tol=1e-12)

    full=(5560.,5644.,1028.42) if layout=='cygno-11x7-v1' else (12616.,2428.,1028.42) if layout=='legacy-25x3' else (2536.,4036.,5599.26)
    expected_vessel=(math.prod(full)-math.prod(x-10 for x in full))*8.96e-6
    # Boolean GetCubicVolume uses Geant4's deterministic Monte Carlo estimator,
    # not exact box subtraction. This is a 5% diagnostic bound, not a replacement
    # for the actual mass. The exporter separately checks exact construction sums.
    discrepancy=q['Vessel']['mass_kg']/expected_vessel-1
    assert abs(discrepancy)<.05,(layout,q['Vessel'],expected_vessel)
    print(layout,'constructed vessel kg=',q['Vessel']['mass_kg'],
          'analytic kg=',expected_vessel,'relative difference=',discrepancy)
    assert math.isclose(q['Resistors']['mass_kg'],counts['Resistors']*1.6*.55*3.2*2.20e-6,rel_tol=1e-12)
    for row in rows:
        expected_quantity=counts['Resistors'] if row['component']=='Resistors' else q[row['component']]['mass_kg']
        assert quantity_for(row,q)==expected_quantity
    for kwargs in [dict(layout='other'),dict(model='thesis-7.3'),dict(geometry_hash='wrong')]:
        args=dict(layout=layout,model='cygno-300elj-v2',geometry_hash=fingerprint)|kwargs
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
        for key,value in dict(EDep_Out=.02,VolNnum_Out=38. if layout=='cygno-11x7-v1' else 37.,X_Vertex=x,Y_Vertex=0.,Z_Vertex=250.25).items():
            vectors[key].clear();vectors[key].push_back(value)
        t.Fill()
    t.Write()
    for key,value in dict(CygnoLayout=layout,CygnoGeometry=fingerprint,CygnoDetectorModel='cygno-300elj-v2',CygnoSourcePolicy='uniform-volume-v1').items():
        ROOT.TNamed(key,value).Write()
    f.Close();return path

plotters=('PlotNormalizedSpectra','PlotNormalizedSpectra_single','PlotNormalizedSpectra_GEMchain')
for layout,q in quantities.items():
    source=fixture(layout)
    config=out/(layout+'-normalization.tsv')
    headers=f'# normalization-format: quantity-v2\n# layout: {layout}\n# detector-model: cygno-300elj-v2\n# source-policy: uniform-volume-v1\n# provenance: synthetic spectra with Table 7.1 and actual constructed quantities; NOT simulated background rates\n'
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
            assert f.Get('Hstack'+suffix).GetHists().GetSize()==len(rows)
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
print('PASS: all v2 assays/chain starts, equilibrium/reset controls, both constructed quantity sets, per-piece normalization, weighted category sums/errors and invalid-unit rejection;',out)
