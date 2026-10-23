"""Historical Acrylic layer activities and actual v2/v3 constructed masses."""
import copy
import csv
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from study import runtime as rt, simulate
from study.source_matrix import read_matrix, validate_matrix, validate_matrix_model, read_quantities


class AcrylicSpecificationTests(unittest.TestCase):
    def test_only_layers_change_and_table_values_match(self):
        v2=read_matrix(rt.REPO/'config/study/cygno-300elj-radioassay-v2.json')
        v3=read_matrix(rt.REPO/'config/study/cygno-300elj-radioassay-v3.json')
        thesis=rt.read(rt.REPO/'config/study/thesis-table7.1.json')
        reference={r['id']:r for r in thesis['contributions']}
        rows={r['id']:r for r in v3['contributions']}
        self.assertEqual(len(rows),26)
        self.assertEqual({r['id'] for r in v2['contributions']}-rows.keys(),
                         {'GEMsCopper_K40','CathodesCopper_K40'})
        for old in v2['contributions']:
            if old['category'] not in ('GEMs','Cathodes'):
                self.assertEqual(rows[old['id']],old)
        for row in rows.values():
            component=row['component']; isotope=row['chain_start']['name']
            if row['category'] not in ('GEMs','Cathodes'): continue
            historical=('GEMsCore' if component.endswith('Polyimide') else
                        'GEMsOuter' if component=='GEMsCopper' else 'Cathodes')
            original=reference[historical+'_'+isotope]
            for key in ('activity','activity_unit','assay_material','activity_basis',
                        'chain_start','stop_before','full_chain','chain_policy','equilibrium_daughters'):
                self.assertEqual(row[key],original[key],(row['id'],key))
        validate_matrix_model(v3,'cygno-acrylic-v3')
        for matrix,model in [(v2,'cygno-acrylic-v3'),(v3,'cygno-300elj-v2')]:
            with self.assertRaisesRegex(ValueError,'matrix/transport'): validate_matrix_model(matrix,model)
        for key,value in [('activity',69.192e-6),('assay_material','300ELJPolyimide'),('activity_basis','separate-material-assay')]:
            bad=copy.deepcopy(v3); bad['contributions'][0][key]=value
            with self.assertRaises(ValueError):validate_matrix(bad)
        config=rt.load_config(rt.REPO/'config/study/cygno-11x7-v3.json')
        self.assertEqual(config['model'],'cygno-acrylic-v3')
        args=simulate.parser().parse_args(['--config',str(rt.REPO/'config/study/cygno-11x7-v3.json'),
            '--matrix',str(rt.REPO/'config/study/cygno-300elj-radioassay-v2.json'),'--list'])
        with self.assertRaisesRegex(ValueError,'matrix/transport'):simulate.run(args)


@unittest.skipUnless(os.environ.get('CYGNO_ACRYLIC_BUILD'),'Set CYGNO_ACRYLIC_BUILD for constructed geometry checks')
class AcrylicGeometryTests(unittest.TestCase):
    def test_material_masses_dimensions_and_external_guard(self):
        build=Path(os.environ['CYGNO_ACRYLIC_BUILD']).resolve()
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp); exports={}; geometries={}
            for model in ('cygno-300elj-v2','cygno-acrylic-v3'):
                output=directory/(model+'.tsv'); geometry=directory/(model+'.json')
                subprocess.run([str(build/'geometry_quantities'),str(output),'cygno-11x7-v1',str(geometry),
                                '--model',model],check=True,capture_output=True,text=True)
                document=rt.read(geometry); geometries[model]=document
                quantities=read_quantities(output,layout='cygno-11x7-v1',model=model,geometry_hash=document['geometry_hash'])
                with output.open() as f:
                    rows={r['component']:r for r in csv.DictReader((l for l in f if not l.startswith('#')),delimiter='\t')}
                exports[model]=rows
                for component,count in [('GEMsPolyimide',462),('CathodesPolyimide',77)]:
                    row=rows[component];acrylic=model=='cygno-acrylic-v3'
                    self.assertEqual(row['geometry_material'],'PMMA' if acrylic else 'G4_KAPTON')
                    self.assertAlmostEqual(float(row['density_g_cm3']),1.19 if acrylic else 1.42)
                    self.assertAlmostEqual(float(row['volume_mm3']),count*500*800*.050)
                    self.assertAlmostEqual(quantities[component]['mass_kg'],count*.4*50e-6*(1190 if acrylic else 1420))
                for core,n in [('GEMsPolyimide',6),('CathodesPolyimide',1)]:
                    row=quantities[core]
                    self.assertAlmostEqual(row['mass_kg']/77,n*(.0238 if model=='cygno-acrylic-v3' else .0284))
            a=geometries['cygno-300elj-v2'];b=geometries['cygno-acrylic-v3']
            self.assertEqual(a | {'model':b['model']},b)
            for component,row in exports['cygno-300elj-v2'].items():
                if component not in ('GEMsPolyimide','CathodesPolyimide'):
                    self.assertEqual(row,exports['cygno-acrylic-v3'][component])
            rejected=subprocess.run([str(build/'rdecay01'),'--mode','external','--model','cygno-acrylic-v3'],capture_output=True,text=True)
            self.assertNotEqual(rejected.returncode,0)
            self.assertIn('internal mode only',rejected.stderr)


if __name__=='__main__':unittest.main()
