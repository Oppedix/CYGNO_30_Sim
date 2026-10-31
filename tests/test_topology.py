"""Detector-topology semantics and full standalone C++ campaign parity.

Synthetic geometry/data only: these checks make no background-rate prediction.
ROOT integration is skipped only when root-config is unavailable.
"""
import copy
import math
import os
import re
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest
import numpy as np
import uproot
from analysis.common.model import Group, GroupVolume, TrackRecord
from analysis.common.topology import SELECTIONS, selection_decisions
from analysis.common.spectra import accumulate, group_energy, histogram_bin, window_flags, WINDOWS
from analysis.common.reporting import CATEGORIES
from study import runtime as rt
from fixtures import campaign_fixture
from compact_fixtures import fixture, tables_from_groups


def geometry(layout):
    count = 150 if layout == 'legacy-25x3' else 154
    return dict(gas_size_mm=[100., 100., 100.],
                gas_centers_mm={str(i): [0., 0., 0.] for i in range(count)})


def group(event=0, x=0., time=0., energy=.02, particle='e-', extra=()):
    return Group(event, particle, 'unused', 'unused',
                 volumes={0: GroupVolume(energy, x, 0., 0., time), **dict(extra)})


def cases():
    """A--M plus zero-active, stored-first, partner-zero and Euclidean checks."""
    yes, multi, veto, outside = (True,)*4, (True,True,False,False), (True,True,True,False), (True,False,False,False)
    return [
        ('A', [group()], [yes]),
        ('B', [group(extra=[(1,GroupVolume(.01,20,0,0,0))])], [multi]),
        ('C', [group(extra=[(1,GroupVolume(0,20,0,0,0))])], [yes]),
        ('D', [group(),group(x=20)], [veto,veto]),
        ('E', [group(),group(x=9)], [yes,yes]),
        ('F', [group(),group(x=10)], [yes,yes]),
        ('G', [group(),group(x=20,time=math.nextafter(1,math.inf))], [yes,yes]),
        ('H', [group(),group(x=20,time=1)], [veto,veto]),
        ('I', [group(event=0),group(event=1,x=20)], [yes,yes]),
        ('J', [group(time=100),group(x=20,time=10000)], [yes,yes]),
        ('K', [group(),group(x=40)], [veto,outside]),
        ('L', [group(),group(extra=[(1,GroupVolume(.01,20,0,0,0))])], [veto,multi]),
        ('M', [group(),group(x=20,particle='alpha'),group(x=20,particle='gamma')],
         [yes,(False,)*4,(False,)*4]),
        ('zero_active', [group(energy=0)], [multi]),
        # Historical fiducial uses first stored volume; candidate uses sole ACTIVE volume.
        ('first_zero', [group(energy=0,extra=[(1,GroupVolume(.01,20,0,0,0))]),group()], [veto,veto]),
        ('zero_partner', [group(),group(x=40,energy=0)], [yes,outside]),
        ('positron', [group(),group(x=20,particle='e+')], [veto,veto]),
        ('same_group_blind_spot', [group(energy=.2)], [yes]),
    ]


def synthetic_groups():
    result = []
    event = 0
    for _, batch, _ in cases():
        # Gamma cannot be produced as a historical compact group; oracle tests
        # explicitly cover it, while ROOT fixtures retain the producer contract.
        span = max(g.event for g in batch)+1
        for g in batch:
            if g.particle == 'gamma':
                continue
            g.event += event
            result.append(g)
        event += span
    # Every bin boundary and both adjacent floats exercise historical N.
    energies = [-1., 0., 10., math.nextafter(10.,math.inf), 400.,
                math.nextafter(400.,math.inf), 2000., 2200.]
    for i in range(1,900):
        edge = i*(2000./900)
        energies.extend([math.nextafter(edge,-math.inf),edge,math.nextafter(edge,math.inf)])
    for energy in energies:
        result.append(group(event=event,energy=energy/1000)); event += 1
    result.append(group(event=event,x=30)); event += 1
    result.append(group(event=event,x=math.nextafter(30,math.inf))); event += 1
    result.append(group(event=event,energy=1e-5,extra=[(1,GroupVolume(.123456789,0,0,0,0))]))
    return result


def oracle(groups, geom, coincidence=1.):
    counts = np.zeros((4,6),dtype=np.int64)
    hist = np.zeros((4,902),dtype=np.int64)
    for g, selected in selection_decisions(groups,geom,coincidence):
        energy = group_energy(g)
        for cut, accepted in enumerate(selected):
            if accepted:
                counts[cut] += window_flags(energy)
                hist[cut,histogram_bin(energy)] += 1
    return counts,hist


class TopologyTests(unittest.TestCase):
    def test_A_through_M_both_layouts(self):
        for layout in ('legacy-25x3','cygno-11x7-v1'):
            for name, groups, expected in cases():
                with self.subTest(layout=layout,case=name):
                    self.assertEqual([flags for _,flags in selection_decisions(groups,geometry(layout))],expected)

    def test_euclidean_and_timing_parameters(self):
        partner = group(x=6)
        partner.volumes[0].y = 8
        self.assertTrue(list(selection_decisions([group(),partner],geometry('legacy-25x3')))[0][1][-1])
        partner.volumes[0].z = 1
        self.assertFalse(list(selection_decisions([group(),partner],geometry('legacy-25x3')))[0][1][-1])
        for parameter in (0,-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError): list(selection_decisions([],{},parameter))
        with self.assertRaises(ValueError):
            list(selection_decisions([group(time=None)],geometry('legacy-25x3')))
        with self.assertRaises(ValueError):
            list(selection_decisions([group(event=1),group(event=0)],geometry('legacy-25x3')))
        self.assertFalse(list(selection_decisions([group(),group(x=20,time=2)],geometry('legacy-25x3'),2))[0][1][-1])

    def test_historical_counts_and_bins_unchanged(self):
        for layout in ('legacy-25x3','cygno-11x7-v1'):
            groups=synthetic_groups(); geom=geometry(layout)
            counts,hist=oracle(groups,geom)
            old_counts,old_hist,_=accumulate(groups,geom)
            np.testing.assert_array_equal(counts[:2],old_counts)
            np.testing.assert_array_equal(hist[:2],old_hist)


def make_campaign(path, layout, model='cygno-300elj-v2', gas_bkg=False):
    config,matrix,campaign=campaign_fixture(path,model,gas_bkg)
    geom=geometry(layout)
    saved_geom=rt.read(path/'geometry.json') | geom | dict(layout=layout)
    config.update(layout=layout,output_mode='compact',output_schema_version=1,primaries_per_job=10000)
    campaign.update(schema_version=3,status='complete',coverage=f'{len(matrix["contributions"])}/{len(matrix["contributions"])}',job_records={})
    campaign['identity']['config']=config
    rt.save(path/'config.json',config); rt.save(path/'geometry.json',saved_geom)
    quantities=(path/'quantities.tsv').read_text().replace('# layout: legacy-25x3', '# layout: '+layout)
    if model == 'cygno-copper-cathode-v4':
        pieces=308 if layout=='cygno-11x7-v1' else 300
        campaign['quantities']['Lens'].update(mass_kg=.512833584772, pieces=pieces)
        quantities=quantities.replace('Lens\t2\t3\t',f'Lens\t.512833584772\t{pieces}\t')
    if gas_bkg and layout == 'cygno-11x7-v1':
        campaign['quantities']['Gas'].update(mass_kg=154e6*1e-6*.0015273872, pieces=154)
        quantities=quantities.replace('Gas\t0.22910808\t150\tCYGNO_gas\t.0015273872\t150000000',
            f'Gas\t{154e6*1e-6*.0015273872}\t154\tCYGNO_gas\t.0015273872\t154000000')
    (path/'quantities.tsv').write_text(quantities)
    expected=dict(layout=layout,model=config['model'],source_policy=config['source_policy'],geometry_hash=saved_geom['geometry_hash'])
    full=synthetic_groups()
    inputs=[]
    for index,row in enumerate(matrix['contributions']):
        # Different per-row efficiencies are essential to test weighted categories.
        groups=copy.deepcopy(full if index%3==0 or row['id']=='Gas_C14' else [group(x=40),group(event=1)] if index%3==1 else [])
        tracks=[]; previous=-1; group_index=0
        for g in groups:
            if g.event!=previous: group_index=0
            g.group_index=group_index; g.step_count=len(g.volumes); g.track_ids={group_index+1}
            tracks.append(TrackRecord(g.event,group_index+1,{'e-':0,'e+':1,'alpha':3}[g.particle],0,g.particle,g.nucleus,g.process,[group_index]))
            previous=g.event; group_index+=1
        attempt='attempt-0002' if index%2 else 'attempt-0007'
        job_path=path/'jobs'/row['id']; attempt_path=job_path/attempt
        data_path='outfiles_V2/compact_t0.root'
        fixture(attempt_path/data_path,expected,records=[],mode='compact',requested=10000,data=tables_from_groups(groups,tracks))
        job=dict(schema_version=3,contribution=row['id'],status='complete',campaign_fingerprint=campaign['fingerprint'],
                 output_mode='compact',output_schema_version=1,workers=1,attempt=attempt,data_path=data_path,
                 requested_primaries=10000,generated_primaries=10000,
                 accounting=dict(RunID=0,RequestedEvents=10000,GeneratedPrimaries=10000,ProcessedEvents=10000,AbortedEvents=0))
        rt.save(job_path/'manifest.json',job);rt.save(attempt_path/'manifest.json',job)
        campaign['job_records'][row['id']]=job
        quantity=campaign['quantities'][row['component']]['mass_kg' if row['activity_unit']=='Bq/kg' else 'pieces']
        scale=row['activity']*quantity*60*60*24*365/10000
        inputs.append((row,scale,groups))
    rt.save(path/'campaign.json',campaign)
    return geom,inputs


@unittest.skipUnless(shutil.which('root-config'),'ROOT required for standalone integration')
class CppTopologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); cls.addClassCleanup(cls.tmp.cleanup)
        cls.root=Path(cls.tmp.name); cls.binary=cls.root/'analysis'
        flags=shlex.split(subprocess.check_output(['root-config','--cflags','--libs'],text=True))
        libdir=Path(subprocess.check_output(['root-config','--libdir'],text=True).strip())
        libraries=['-lRooFitHS3']
        if list(libdir.glob('libRooFitJSONInterface.*')): libraries.append('-lRooFitJSONInterface')
        subprocess.run(['c++','-O3','-std=c++17','-ffp-contract=off',str(rt.REPO/'analysis/common_c++/AnalyzeCompactCampaign.cpp'),
                        '-I'+str(rt.REPO),*flags,*libraries,'-o',str(cls.binary)],check=True,capture_output=True)
        source=(rt.REPO/'analysis/common_c++/AnalyzeCompactCampaign.cpp').read_text()
        source=re.sub(r'        // BEGIN additional stack figures.*?        // END additional stack figures',
                      '',source,flags=re.S)
        source=re.sub(r'    // BEGIN additional overlay figures.*?    // END additional overlay figures',
                      '',source,flags=re.S)
        baseline_source=cls.root/'without_extra_figures.cpp'; baseline_source.write_text(source)
        cls.baseline=cls.root/'baseline'
        subprocess.run(['c++','-O3','-std=c++17','-ffp-contract=off',str(baseline_source),
                        '-I'+str(rt.REPO),*flags,*libraries,'-o',str(cls.baseline)],check=True,capture_output=True)


    def run_analysis(self,campaign,output,*args,binary=None):
        run=subprocess.run([str(binary or self.binary),str(campaign),str(output),*args],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    def test_figures_leave_all_histograms_and_counters_unchanged(self):
        campaign=self.root/'figure-campaign';make_campaign(campaign,'cygno-11x7-v1')
        before=self.root/'figure-before';after=self.root/'figure-after'
        self.run_analysis(campaign,before,binary=self.baseline)
        self.run_analysis(campaign,after)
        self.check_baseline(before,after)
        self.assertEqual(len(list((after/'figures').rglob('*.png'))),10)
        self.assertEqual(len(list((after/'figures').rglob('*.pdf'))),10)

    def test_invalid_coincidence(self):
        for value in ('0','-1','nan','inf','1junk'):
            run=subprocess.run([str(self.binary),'missing','unused','--coincidence-ns',value],capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0)
            self.assertIn('positive and finite',run.stderr)

    def test_full_campaign_parity_and_reports(self):
        for layout in ('legacy-25x3','cygno-11x7-v1'):
            campaign=self.root/layout; geom,inputs=make_campaign(campaign,layout)
            for coincidence in (1.,2.):
                with self.subTest(layout=layout,coincidence=coincidence):
                    output=self.root/(layout+'-'+str(coincidence))
                    args=[] if coincidence==1 else ['--coincidence-ns',str(coincidence)]
                    self.run_analysis(campaign,output,*args)
                    expected=[(row,scale,*oracle(groups,geom,coincidence)) for row,scale,groups in inputs]
                    self.check_output(output,expected,coincidence)
                    baseline=os.environ.get('CYGNO_HISTORICAL_BINARY')
                    if baseline and coincidence==1:
                        before=self.root/(layout+'-before');self.run_analysis(campaign,before,binary=baseline)
                        self.check_baseline(before,output)

    def test_acrylic_v3_parity_and_model_rejection(self):
        campaign=self.root/'acrylic-campaign'
        geom,inputs=make_campaign(campaign,'cygno-11x7-v1','cygno-acrylic-v3')
        output=self.root/'acrylic-analysis'
        snapshots={p:p.read_bytes() for p in campaign.rglob('*') if p.is_file()}
        self.run_analysis(campaign,output)
        expected=[(row,scale,*oracle(groups,geom)) for row,scale,groups in inputs]
        self.check_output(output,expected,1.)
        scenario=rt.read(output/'normalization-scenario.json')
        self.assertEqual(scenario['detector_model'],'cygno-acrylic-v3')
        self.assertEqual(scenario['scenario_id'],'cygno-300elj-radioassay-v3')
        with uproot.open(output/'analysis.root') as f:
            self.assertEqual(str(f['provenance/matrix.json']), (campaign/'matrix.json').read_text())
            self.assertEqual(f['provenance/NormalizationScenario'].member('fTitle'),scenario['scenario_id'])
        self.assertEqual(snapshots,{p:p.read_bytes() for p in snapshots})
        # Even internally consistent manifests cannot relabel v3 sources as v4 transport.
        config=rt.read(campaign/'config.json'); config['model']='cygno-copper-cathode-v4'
        rt.save(campaign/'config.json',config)
        document=rt.read(campaign/'campaign.json');document['identity']['config']=config
        rt.save(campaign/'campaign.json',document)
        rejected=self.root/'acrylic-rejected'
        run=subprocess.run([str(self.binary),str(campaign),str(rejected)],capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)
        self.assertFalse(rejected.exists())

    def test_copper_cathode_v4_parity_and_model_rejection(self):
        campaign=self.root/'v4-campaign'
        geom,inputs=make_campaign(campaign,'cygno-11x7-v1','cygno-copper-cathode-v4')
        output=self.root/'v4-analysis'
        snapshots={p:p.read_bytes() for p in campaign.rglob('*') if p.is_file()}
        self.run_analysis(campaign,output)
        expected=[(row,scale,*oracle(groups,geom)) for row,scale,groups in inputs]
        self.check_output(output,expected,1.)
        scenario=rt.read(output/'normalization-scenario.json')
        self.assertEqual(scenario['detector_model'],'cygno-copper-cathode-v4')
        self.assertEqual(scenario['scenario_id'],'cygno-radioassay-v4')
        with uproot.open(output/'analysis.root') as f:
            self.assertEqual(str(f['provenance/matrix.json']), (campaign/'matrix.json').read_text())
            self.assertEqual(f['provenance/NormalizationScenario'].member('fTitle'),scenario['scenario_id'])
        self.assertEqual(snapshots,{p:p.read_bytes() for p in snapshots})
        # Even internally consistent manifests cannot relabel v4 sources as v3 transport.
        config=rt.read(campaign/'config.json'); config['model']='cygno-acrylic-v3'
        rt.save(campaign/'config.json',config)
        document=rt.read(campaign/'campaign.json');document['identity']['config']=config
        rt.save(campaign/'campaign.json',document)
        rejected=self.root/'v4-rejected'
        run=subprocess.run([str(self.binary),str(campaign),str(rejected)],capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)
        self.assertFalse(rejected.exists())

    def test_gas_v4_all_selections_stacks_and_rejection(self):
        campaign=self.root/'gas-campaign'
        geom,inputs=make_campaign(campaign,'legacy-25x3','cygno-copper-cathode-v4',gas_bkg=True)
        output=self.root/'gas-analysis'
        self.run_analysis(campaign,output)
        self.check_output(output,[(row,scale,*oracle(groups,geom)) for row,scale,groups in inputs],1.)
        self.assertEqual(rt.read(output/'normalization-scenario.json')['scenario_id'],'cygno-radioassay-v4-gas-v1')
        config=rt.read(campaign/'config.json');config.pop('gas_bkg')
        rt.save(campaign/'config.json',config)
        document=rt.read(campaign/'campaign.json');document['identity']['config']=config
        rt.save(campaign/'campaign.json',document)
        rejected=self.root/'gas-rejected'
        run=subprocess.run([str(self.binary),str(campaign),str(rejected)],capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)
        self.assertFalse(rejected.exists())

    def test_gas_chain_metadata_requires_literal_null_and_pb210(self):
        campaign=self.root/'gas-json-campaign'
        geom,inputs=make_campaign(campaign,'cygno-11x7-v1','cygno-copper-cathode-v4',gas_bkg=True)
        original=rt.read(campaign/'matrix.json')
        # Keep both snapshots consistent so rejection must come from scientific validation.
        cases=[('Gas_C14',value) for value in ({},[], '', 'null',False,0,{'Z':7,'A':14,'name':'N14'})]
        cases += [('Gas_C14','missing'),('Gas_Rn222',None),
                  ('Gas_Rn222',{'Z':82,'A':210,'name':'Bi210'})]
        for index,(contribution,value) in enumerate(cases):
            with self.subTest(contribution=contribution,value=value):
                matrix=copy.deepcopy(original)
                row=next(r for r in matrix['contributions'] if r['id']==contribution)
                if value=='missing': row.pop('stop_before')
                else: row['stop_before']=value
                rt.save(campaign/'matrix.json',matrix)
                document=rt.read(campaign/'campaign.json');document['identity']['matrix']=matrix
                rt.save(campaign/'campaign.json',document)
                output=self.root/f'gas-json-rejected-{index}'
                run=subprocess.run([str(self.binary),str(campaign),str(output)],capture_output=True,text=True)
                self.assertNotEqual(run.returncode,0,run.stdout+run.stderr)
                if contribution=='Gas_C14' and value!='missing':
                    self.assertIn('C14 must reach stable N14',run.stderr)
                self.assertFalse(output.exists())
        rt.save(campaign/'matrix.json',original)
        document['identity']['matrix']=original;rt.save(campaign/'campaign.json',document)
        snapshots={p:p.read_bytes() for p in campaign.rglob('*') if p.is_file()}
        output=self.root/'gas-json-valid'
        self.run_analysis(campaign,output)
        self.check_output(output,[(row,scale,*oracle(groups,geom)) for row,scale,groups in inputs],1.)
        with uproot.open(output/'analysis.root') as file:
            self.assertEqual(str(file['provenance/matrix.json']),(campaign/'matrix.json').read_text())
        self.assertEqual(snapshots,{p:p.read_bytes() for p in snapshots})

    def check_output(self, output, expected, coincidence):
        for name in ('figure7.5','figure7.6','figure_multivolume_veto','figure_multisite_veto'):
            for ext in ('png','pdf'): self.assertGreater((output/(name+'.'+ext)).stat().st_size,100)
        report=(output/'cutflow.md').read_text()
        # Split only main headings, since subsection headings have three hashes.
        stages=[s for s in report.split('\n## ') if s[:1] in '1234' and s[:1]]
        self.assertEqual(len(stages),4)
        with uproot.open(output/'analysis.root') as f:
            self.assertEqual(f['provenance/CoincidenceWindow_ns'].member('fVal'),coincidence)
            self.assertEqual(f['provenance/MultisiteDistance_mm'].member('fVal'),10.)
            new=f['SelectionEnergyWindows'].arrays(library='np'); old=f['ExactEnergyWindows'].arrays(library='np')
            normalization=f['Normalization'].arrays(library='np')
            self.assertEqual(len(new['Count']),len(expected)*4*6);self.assertEqual(len(old['Count']),len(expected)*2*6)
            categories=CATEGORIES + (('Gas C14','Gas Rn222') if any(row['component']=='Gas' for row,*_ in expected) else ())
            rates=np.zeros((4,len(categories))); raw_counts=np.zeros_like(rates)
            hist=np.zeros((4,len(categories),902)); variance=np.zeros_like(hist)
            for row,scale,counts,bins in expected:
                mask=normalization['Contribution']==row['id']
                self.assertEqual(normalization['Scale'][mask].tolist(),[scale])
                self.assertEqual(normalization['Activity'][mask].tolist(),[row['activity']])
                c=categories.index(row['category'])
                for cut,selection in enumerate(SELECTIONS):
                    np.testing.assert_array_equal(f['contributions/'+row['id']+'/raw_'+selection].values(flow=True),bins[cut])
                    for w,window in enumerate(WINDOWS):
                        mask=(new['Contribution']==row['id']) & (new['Selection']==selection) & (new['Window']==window)
                        self.assertEqual(new['Count'][mask].tolist(),[counts[cut,w]])
                        self.assertEqual(new['RatePerYear'][mask].tolist(),[counts[cut,w]*scale])
                        self.assertEqual(new['VariancePerYear2'][mask].tolist(),[counts[cut,w]*scale*scale])
                    rates[cut,c]+=counts[cut,0]*scale;raw_counts[cut,c]+=counts[cut,0]
                    hist[cut,c]+=bins[cut]*scale;variance[cut,c]+=bins[cut]*scale*scale
                    line=next(line for line in stages[cut].splitlines() if line.startswith('| '+row['id']+' |'))
                    fields=[v.strip() for v in line.split('|')[1:-1]]
                    self.assertEqual(int(fields[3]),counts[cut,0]);self.assertEqual(float(fields[4]),float(f'{counts[cut,0]*scale:.10g}'))
                    prev=counts[max(0,cut-1),0]
                    self.assertEqual(fields[5],'n/a' if prev==0 else f'{100.*(counts[cut,0]*scale)/(prev*scale):.6f}')
            widths=np.ones(902);widths[1:-1]=2000./900
            weighted_diff=False
            for cut,selection in enumerate(SELECTIONS):
                total=np.zeros(902)
                for c,category in enumerate(categories):
                    h=f[selection+'/categories/'+category]
                    np.testing.assert_array_equal(h.values(flow=True),hist[cut,c]/widths)
                    np.testing.assert_array_equal(h.errors(flow=True),np.sqrt((np.sqrt(variance[cut,c])/widths)**2))
                    total+=hist[cut,c]/widths
                    line=next(line for line in stages[cut].splitlines() if line.startswith('| '+category+' |'))
                    fields=[v.strip() for v in line.split('|')[1:-1]]
                    self.assertEqual(float(fields[1]),float(f'{rates[cut,c]:.10g}'))
                    for col,den_cut in ((2,max(0,cut-1)),(3,0)):
                        den=rates[den_cut,c]
                        self.assertEqual(fields[col],'n/a' if den==0 else f'{100.*rates[cut,c]/den:.6f}')
                    if cut and raw_counts[cut-1,c] and rates[cut-1,c]:
                        weighted_diff |= abs(rates[cut,c]/rates[cut-1,c]-raw_counts[cut,c]/raw_counts[cut-1,c])>1e-6
                np.testing.assert_array_equal(f[selection+'/total'].values(flow=True),total)
            self.assertTrue(weighted_diff,'Fixture must distinguish normalized-rate and raw-count efficiency')
            mask=np.isin(new['Selection'],SELECTIONS[:2])
            for field in ('Contribution','Category','Window','Count','RatePerYear','VariancePerYear2'):
                np.testing.assert_array_equal(old[field],new[field][mask])

    def check_baseline(self,before,after):
        for name in ('figure7.5.png','figure7.6.png','figure_multivolume_veto.png','figure_multisite_veto.png'):
            self.assertEqual((before/name).read_bytes(),(after/name).read_bytes(),name)
        with uproot.open(before/'analysis.root') as old,uproot.open(after/'analysis.root') as new:
            for key in old.keys(recursive=True,cycle=False):
                obj=old[key]
                if getattr(obj,'classname',None)=='TH1D':
                    np.testing.assert_array_equal(obj.values(flow=True),new[key].values(flow=True))
                    np.testing.assert_array_equal(obj.errors(flow=True),new[key].errors(flow=True))
                elif getattr(obj,'classname',None)=='TTree':
                    for field,values in obj.arrays(library='np').items():
                        np.testing.assert_array_equal(values,new[key][field].array(library='np'))
