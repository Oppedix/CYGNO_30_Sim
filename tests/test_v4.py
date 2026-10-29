"""Current detector contract: copper cathode and physical-lens per-piece activity."""
import copy
import csv
from decimal import Decimal
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from study import runtime as rt, simulate
from study.source_matrix import (read_matrix, validate_matrix, validate_matrix_model,
                                read_quantities, quantity_for, LENS_PROVENANCE)
from analysis.common.normalization import scale_for

MODEL = 'cygno-copper-cathode-v4'
MATRIX = 'cygno-radioassay-v4'


class V4SpecificationTests(unittest.TestCase):
    def test_sources_lens_units_and_exact_conversion(self):
        matrix=read_matrix(rt.REPO/'config/study'/f'{MATRIX}.json')
        self.assertEqual(len(matrix['contributions']),23)
        self.assertEqual(matrix['provenance']['lens'],LENS_PROVENANCE)
        self.assertEqual(LENS_PROVENANCE['source'],'CYGNO_radioactivity_excel_suprasil')
        expected={'U238':('1.23e-4','4.72689e-4'), 'Th232':('4.07e-5','1.564101e-4'),
                  'K40':('3.10e-4','1.19133e-3')}
        quantities={'Lens':dict(mass_kg=.512833584772,pieces=308)}
        for row in matrix['contributions']:
            self.assertNotIn(row['component'],('CathodesPolyimide','CathodesCopper'))
            if row['component']=='Lens':
                specific,activity=expected[row['chain_start']['name']]
                self.assertEqual(Decimal(specific)*Decimal('3.843'),Decimal(activity))
                self.assertEqual(row['activity'],float(activity))
                self.assertEqual(row['activity_unit'],'Bq/piece')
                self.assertEqual(quantity_for(row,quantities),308)
                scale=scale_for(row,quantities,100)
                self.assertEqual(scale,row['activity']*308*60*60*24*365/100)
                quantities['Lens']['mass_kg']*=1000
                self.assertEqual(scale_for(row,quantities,100),scale)
                for key,value in [('activity_unit','Bq/kg'),('activity',float(specific)),
                                  ('activity',row['activity']*3.843),('provenance','other')]:
                    bad=copy.deepcopy(matrix)
                    next(r for r in bad['contributions'] if r['id']==row['id'])[key]=value
                    with self.assertRaises(ValueError):validate_matrix(bad)
            if row['component']=='Cathode':
                self.assertEqual(row['assay_material'],'EFCu')
                self.assertEqual(row['activity_unit'],'Bq/kg')
        validate_matrix_model(matrix,MODEL)
        old=read_matrix(rt.REPO/'config/study/cygno-300elj-radioassay-v3.json')
        with self.assertRaisesRegex(ValueError,'matrix/transport'):validate_matrix_model(old,MODEL)
        for version in ('cygno-acrylic-v3','cygno-300elj-v2'):
            with self.assertRaisesRegex(ValueError,'matrix/transport'):validate_matrix_model(matrix,version)
        for name in ('samuele','smoke-A','smoke-B','cygno-11x7-v4'):
            self.assertEqual(rt.load_config(rt.REPO/'config/study'/f'{name}.json')['model'],MODEL)
        args=simulate.parser().parse_args(['--list'])
        with patch('builtins.print') as printed: self.assertEqual(simulate.run(args),0)
        self.assertEqual(printed.call_count,23)

    def test_old_campaign_rejected_before_writes_or_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);output=root/'campaign';output.mkdir();build=root/'build';build.mkdir()
            for name in ('rdecay01','geometry_quantities'):(build/name).touch()
            rt.save(output/'campaign.json',dict(identity=dict(config=dict(model='cygno-acrylic-v3'))))
            before={p:p.read_bytes() for p in output.rglob('*') if p.is_file()}
            args=simulate.parser().parse_args(['--build',str(build),'--output',str(output)])
            with patch.object(rt,'invoke',side_effect=AssertionError('Must not launch')):
                with self.assertRaisesRegex(ValueError,'new physics'):simulate.run(args)
            self.assertEqual(before,{p:p.read_bytes() for p in output.rglob('*') if p.is_file()})
            from external.study import simulate as ext
            from types import SimpleNamespace
            args=SimpleNamespace(config=rt.REPO/'external/config/hall-c-gamma-2026-proxy.json',
                build=build, output=output, model=None, primaries=None, seed=None,
                shield=None, output_mode=None, dry_run=False, retry_failed=False)
            with patch.object(rt,'invoke',side_effect=AssertionError('Must not launch')):
                with self.assertRaisesRegex(ValueError,'new physics'):ext.run(args)
            self.assertEqual(before,{p:p.read_bytes() for p in output.rglob('*') if p.is_file()})


@unittest.skipUnless(os.environ.get('CYGNO_ACRYLIC_BUILD'),'Set CYGNO_ACRYLIC_BUILD for constructed geometry')
class V4GeometryTests(unittest.TestCase):
    def test_constructed_geometry_export_and_unchanged_optics(self):
        build=Path(os.environ['CYGNO_ACRYLIC_BUILD'])
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for layout,count in [('legacy-25x3',75),('cygno-5x5x3-v1',75),('cygno-11x7-v1',77)]:
                exports={};audits={}
                for mode,model in [('internal','cygno-acrylic-v3'),('internal',MODEL),('external',MODEL)]:
                    stem=root/f'{layout}-{mode}-{model}';table=stem.with_suffix('.tsv');geometry=stem.with_suffix('.json')
                    flags=['--model',model,'--mode',mode]
                    subprocess.run([str(build/'geometry_quantities'),str(table),layout,str(geometry),*flags],
                                   check=True,capture_output=True,text=True)
                    with table.open() as f:
                        rows={r['component']:r for r in csv.DictReader((l for l in f if not l.startswith('#')),delimiter='\t')}
                    exports[mode,model]=rows
                    audit=stem.with_suffix('.audit.tsv')
                    subprocess.run([str(build/'validation/geometry_audit'),str(audit),'--layout',layout,*flags],
                                   check=True,capture_output=True,text=True)
                    with audit.open() as f:audits[mode,model]=list(csv.DictReader(f,delimiter='\t'))
                    if model!=MODEL:continue
                    d=rt.read(geometry)
                    if mode=='internal':
                        read_quantities(table,layout=layout,model=model,geometry_hash=d['geometry_hash'])
                    counts=dict(Cathode=count,GEMsPolyimide=6*count,GEMsCopper=12*count,RingSupports=2*count,
                                RingStrips=50*count,Resistors=52*count,Lens=4*count,Sensors=4*count,Vessel=1)
                    self.assertEqual({k:int(v['pieces']) for k,v in rows.items()},counts)
                    self.assertEqual(rows['Cathode']['geometry_material'],'G4_Cu')
                    self.assertAlmostEqual(float(rows['Cathode']['mass_kg']),count*.4*60e-6*8960,places=10)
                    self.assertAlmostEqual(float(rows['Cathode']['volume_mm3']),count*500*800*.060,places=7)
                    self.assertEqual(rows['GEMsPolyimide']['geometry_material'],'PMMA')
                    self.assertAlmostEqual(float(rows['GEMsPolyimide']['mass_kg']),6*count*.0238,places=10)
                    for row in rows.values():
                        self.assertAlmostEqual(float(row['volume_mm3'])*float(row['density_g_cm3'])*1e-6,
                                               float(row['mass_kg']),places=9)
                self.assertEqual(exports['internal',MODEL],exports['external',MODEL])
                self.assertEqual([r for r in audits['internal',MODEL] if r['logical']!='World'],
                                 [r for r in audits['external',MODEL] if r['logical']!='World'])
                old=audits['internal','cygno-acrylic-v3'];new=audits['internal',MODEL]
                self.assertEqual(len(new),count*137+2)
                self.assertFalse(any(r['logical'] in ('CathodesPolyimide','CathodesCopper') for r in new))
                cathodes=[r for r in new if r['logical']=='Cathode']
                self.assertEqual(len(cathodes),count)
                self.assertTrue(all(abs(float(r['zmax'])-.030)<1e-12 for r in cathodes))
                self.assertEqual([r for r in old if r['logical'] not in ('CathodesPolyimide','CathodesCopper')],
                                 [r for r in new if r['logical']!='Cathode'])
                self.assertEqual(exports['internal','cygno-acrylic-v3']['Lens'],exports['internal',MODEL]['Lens'])

if __name__=='__main__':unittest.main()
