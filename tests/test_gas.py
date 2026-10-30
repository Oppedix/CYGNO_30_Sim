"""Gas scenario contracts and full offline workflow; fixtures are not transport."""
import copy
import io
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from study import runtime as rt, simulate
from study.source_matrix import (read_matrix, validate_matrix, with_gas_backgrounds,
    GAS_C14_ACTIVITY, GAS_CARBON_MASS_FRACTION, GAS_PROVENANCE, decay_commands, read_quantities)
from study.campaign import validate_campaign
from study.analyze import analyze
from study.archive import package, open_campaign
from fixtures import campaign_fixture, fake_invoke

MODEL = 'cygno-copper-cathode-v4'


class GasTests(unittest.TestCase):
    def test_science_matrix_controls_and_default_macros(self):
        base = read_matrix(rt.REPO/'config/study/cygno-radioassay-v4.json')
        original = copy.deepcopy(base)
        gas = with_gas_backgrounds(base)
        self.assertEqual(base, original)
        self.assertEqual(len(gas['contributions']), 25)
        self.assertEqual(gas['contributions'][:23], base['contributions'])
        self.assertEqual(validate_matrix(gas), gas)
        # Independently count CF4 molecules per kg mixture from the partial density.
        cf4_mass_kg = 1429.8944/1527.3872
        c12_atoms = cf4_mass_kg*1000/88.0027*6.02214076e23*.9893
        expected = c12_atoms*1.94e-18*math.log(2)/(5730*31536000)
        self.assertAlmostEqual(GAS_C14_ACTIVITY, expected, places=18)
        self.assertAlmostEqual(GAS_CARBON_MASS_FRACTION, .1277694840552402)
        for row in gas['contributions'][-2:]:
            self.assertEqual(row['activity_unit'], 'Bq/kg')
            controls = decay_commands(row)
            self.assertIn('/detector/RadElement Gas', controls)
            self.assertIn('/stopChain/ZStopDecay '+('82' if row['id']=='Gas_Rn222' else '0'), controls)
        for field, value in [('activity', 1.), ('category', 'GEMs'), ('stop_before', None)]:
            bad = copy.deepcopy(gas); bad['contributions'][-1][field] = value
            with self.assertRaises(ValueError): validate_matrix(bad)
        bad = copy.deepcopy(gas); bad['provenance']['gas']['Rn222']['doi'] = 'other'
        with self.assertRaises(ValueError): validate_matrix(bad)
        configs = []
        for flag in ([], ['--gas-bkg','no'], ['--gas-bkg','yes']):
            macros = io.StringIO()
            with redirect_stdout(macros):
                self.assertEqual(simulate.run(simulate.parser().parse_args(['--list',*flag])), 0)
            configs.append(macros.getvalue())
        self.assertEqual(configs[0], configs[1])
        self.assertTrue(configs[2].startswith(configs[0]))

    def test_both_resume_directions_rejected_before_writes(self):
        for saved_gas, flag in ((True,'no'), (False,'yes')):
            with self.subTest(saved_gas=saved_gas), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); output = root/'campaign'
                campaign_fixture(output, MODEL, saved_gas)
                build = root/'build'; build.mkdir()
                for name in ('rdecay01','geometry_quantities'): (build/name).touch()
                before = {p:p.read_bytes() for p in output.rglob('*') if p.is_file()}
                args = simulate.parser().parse_args(['--build',str(build),'--output',str(output),'--gas-bkg',flag])
                with patch.object(rt,'invoke',side_effect=AssertionError('No transport')):
                    with self.assertRaisesRegex(ValueError,'new output directory'): simulate.run(args)
                self.assertEqual(before, {p:p.read_bytes() for p in before})

    def test_all_storage_modes_analysis_archive_stacks_and_provenance(self):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            base = Path(directory); spectra = []
            for mode in ('raw','compact','both'):
                root = base/mode
                config, matrix, campaign = campaign_fixture(root, MODEL, True)
                config.update(output_mode=mode, output_schema_version=1)
                rt.save(root/'config.json', config)
                campaign.update(schema_version=3, fingerprint=rt.object_digest(campaign['identity']))
                campaign['snapshots']['config.json'] = rt.digest(root/'config.json')
                rt.save(root/'campaign.json',campaign)
                with patch.object(rt,'invoke',side_effect=fake_invoke):
                    for row in matrix['contributions']: simulate.run_job(root,row,config,campaign,'fixture')
                simulate.update_campaign(root,campaign,matrix)
                self.assertEqual(len(validate_campaign(root)), 25)
                with patch.object(rt,'invoke',side_effect=AssertionError('Reuse complete job')):
                    row=matrix['contributions'][-1]
                    self.assertEqual(simulate.run_job(root,row,config,campaign,'fixture')['attempt'],'attempt-0001')
                output=base/(mode+'-analysis')
                self.assertEqual(analyze(root,output),0)
                data=rt.read(output/'spectra.json'); spectra.append(data)
                self.assertEqual({r['category'] for r in data['density']},
                                 {r['category'] for r in matrix['contributions']})
                for cut in (0,1):
                    rates=[r['rate_per_year'] for r in data['categories'] if r['fiducial']==cut and r['window']=='all']
                    total=next(r['rate_per_year'] for r in data['totals'] if r['fiducial']==cut and r['window']=='all')
                    self.assertTrue(math.isclose(sum(rates),total,rel_tol=1e-14))
                tables=rt.read(output/'tables.json')['table7_3']
                self.assertEqual(len(tables),18)
                self.assertTrue(all(r['published_reference_counts_per_year'] is None
                                    for r in tables if r['category'].startswith('Gas ')))
                self.assertEqual(rt.read(output/'matrix.json')['provenance']['gas'], GAS_PROVENANCE)
                if mode == 'compact':
                    notebook=json.loads((rt.REPO/'analysis/common/CYGNO30_background_analysis_walkthrough.ipynb').read_text())
                    namespace={'__name__':'__notebook__'}
                    try:
                        for cell in notebook['cells']:
                            if cell['cell_type']=='code':
                                source=''.join(cell['source']).replace('CAMPAIGN_DIR = None',f'CAMPAIGN_DIR = {str(root)!r}')
                                exec(compile(source,'gas-campaign-walkthrough','exec'),namespace)
                        self.assertEqual(namespace['spectra'],data)
                        self.assertEqual(namespace['summary']['coverage'],'25/25')
                        self.assertEqual(len(rt.read(namespace['OUTPUT_DIR']/'tables.json')['table7_3']),18)
                    finally:
                        if 'output_directory' in namespace: namespace['output_directory'].cleanup()
                for name in ('figure7.5','figure7.6'):
                    for suffix in ('.png','.pdf'): self.assertGreater((output/(name+suffix)).stat().st_size,100)
                with open_campaign(package(root)) as unpacked:
                    self.assertEqual(len(validate_campaign(unpacked)),25)
            self.assertEqual(spectra[0],spectra[1]); self.assertEqual(spectra[1],spectra[2])


@unittest.skipUnless(os.environ.get('CYGNO_ACRYLIC_BUILD'), 'Set CYGNO_ACRYLIC_BUILD for Geant4 quantities')
class GasQuantitiesTests(unittest.TestCase):
    def test_actual_mass_and_default_export_unchanged(self):
        binary=Path(os.environ['CYGNO_ACRYLIC_BUILD'])/'geometry_quantities'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for layout,modules in [('legacy-25x3',75),('cygno-5x5x3-v1',75),('cygno-11x7-v1',77)]:
                exports=[]
                for flag in ([],['--gas-bkg','no'],['--gas-bkg','yes']):
                    table=root/'quantities.tsv'; geom=root/'geometry.json'
                    subprocess.run([binary,table,layout,geom,'--model',MODEL,*flag],check=True,capture_output=True)
                    geometry=rt.read(geom)
                    quantities=read_quantities(table,layout=layout,model=MODEL,geometry_hash=geometry['geometry_hash'],gas_bkg='yes' in flag)
                    exports.append(table.read_text())
                    if 'yes' in flag:
                        gas=quantities.pop('Gas')
                        self.assertEqual(gas['pieces'],2*modules)
                        self.assertAlmostEqual(gas['mass_kg'],2*modules*.5*.8*.5*1.5273872)
                        material=read_quantities(root/'no.tsv',layout=layout,model=MODEL,geometry_hash=geometry['geometry_hash'])
                        self.assertEqual(quantities,material)
                    else: (root/'no.tsv').write_bytes(table.read_bytes())
                self.assertEqual(exports[0],exports[1])


@unittest.skipUnless(os.environ.get('CYGNO_GAS_TRANSPORT_BUILD'), 'Set CYGNO_GAS_TRANSPORT_BUILD for real decay transport')
class GasTransportTests(unittest.TestCase):
    def test_real_decays_endpoint_chain_boundary_and_storage_parity(self):
        import numpy as np
        import uproot
        from analysis.common.inputs import canonical_input
        from analysis.common.spectra import accumulate
        build=Path(os.environ['CYGNO_GAS_TRANSPORT_BUILD']).resolve()
        parent=build/'validation-results';parent.mkdir(exist_ok=True)
        root=Path(tempfile.mkdtemp(prefix='gas-transport-',dir=parent))
        print('Retained gas transport evidence: '+str(root),flush=True)
        subprocess.run([build/'geometry_quantities',root/'quantities.tsv','cygno-11x7-v1',root/'geometry.json',
                        '--model',MODEL,'--gas-bkg','yes'],check=True,stdout=subprocess.DEVNULL)
        geometry=rt.read(root/'geometry.json')
        expected=dict(layout='cygno-11x7-v1',model=MODEL,source_policy='uniform-volume-v1',geometry_hash=geometry['geometry_hash'])
        config=rt.load_config(rt.REPO/'config/study/cygno-11x7-v4.json') | dict(primaries_per_job=100)
        rows=with_gas_backgrounds(read_matrix(rt.REPO/'config/study/cygno-radioassay-v4.json'))['contributions'][-2:]
        for row in rows:
            values=[]
            for mode in ('raw','compact','both'):
                folder=root/(row['id']+'-'+mode);folder.mkdir()
                macro=folder/'run.mac';macro.write_text(rt.macro_for(row,config | dict(output_mode=mode)))
                log=rt.invoke([build/'rdecay01',macro,'1','--layout',config['layout'],'--model',MODEL,
                               '--output-mode',mode],folder,'simulation',120)
                self.assertNotIn('PART122',log)
                rt.validate_simulation_log(log,rt.parse_environment(log),100)
                if row['id']=='Gas_C14': self.assertRegex(log,r'\bN14\s*:')
                else:
                    for daughter in ('Po218','Pb214','Bi214','Po214','Pb210'): self.assertRegex(log,r'\b'+daughter+r'\s*:')
                    self.assertNotRegex(log,r'\b(?:Bi210|Po210)\s*:')
                data=next((folder/'outfiles_V2').glob('*.root'))
                with uproot.open(data) as file:
                    _,stream,_=canonical_input(file,expected,100,geometry,'64 MB',mode,1)
                    groups=list(stream)
                    if row['id']=='Gas_C14':
                        self.assertTrue(any(g.particle=='e-' for g in groups))
                        self.assertTrue(all(sum(v.energy for v in g.volumes.values())<=.157 for g in groups if g.particle=='e-'))
                    counts,hist,_=accumulate(groups,geometry);values.append((counts,hist))
            for counts,hist in values[1:]:
                np.testing.assert_array_equal(counts,values[0][0]);np.testing.assert_array_equal(hist,values[0][1])


if __name__ == '__main__': unittest.main()
