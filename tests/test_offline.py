import io
import json
import math
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import uproot
from study import runtime as rt, simulate
from analysis.raw.io import inspect_raw, LEGACY_HITS_SCHEMA as HITS_SCHEMA
from analysis.raw.preprocess import groups
from analysis.common.spectra import accumulate, fiducial, scale_for, summarize, window_flags
from study.campaign import validate_campaign
from study.archive import extract, package, open_campaign
from study.analyze import analyze
from fixtures import chunk, raw_fixture, campaign_fixture, fake_invoke


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'raw.root'
        self.expected = dict(layout='legacy-25x3', model='code-compatible', source_policy='historical', geometry_hash='fixture')

    def test_empty_and_nonempty(self):
        for rows in [[], [{}]]:
            raw_fixture(self.path, self.expected, rows)
            self.assertEqual(inspect_raw(self.path, self.expected, 2, 1)['hit_rows'], len(rows))

    def test_bad_data(self):
        for row in [dict(EventNumber=-1), dict(EventNumber=2), dict(VolumeNumber=-1), dict(VolumeNumber=150),
                    dict(EnergyDeposit=float('nan')), dict(x_hits=float('inf'))]:
            raw_fixture(self.path, self.expected, [row])
            with self.assertRaises(ValueError): inspect_raw(self.path, self.expected, 2, 1)
        raw_fixture(self.path, self.expected, [dict(EventNumber=1),dict(EventNumber=0)])
        with self.assertRaises(ValueError): inspect_raw(self.path, self.expected, 2, 1)

    def test_metadata_accounting_row_counts(self):
        for kwargs in [dict(metadata_rows=0),dict(metadata_rows=2),dict(accounting_rows=0),dict(accounting_rows=2)]:
            raw_fixture(self.path, self.expected, **kwargs)
            with self.assertRaises(ValueError): inspect_raw(self.path, self.expected, 2)

    def test_schema_accounting_identity(self):
        for field in ['GeneratedPrimaries', 'ProcessedEvents', 'AbortedEvents', 'RequestedEvents', 'RunID']:
            raw_fixture(self.path, self.expected, accounting={field:1})
            with self.assertRaises(ValueError): inspect_raw(self.path, self.expected, 2)
        raw_fixture(self.path, self.expected, schema=HITS_SCHEMA | {'EnergyDeposit':'float32'})
        with self.assertRaises(ValueError): inspect_raw(self.path, self.expected, 2)
        raw_fixture(self.path, self.expected)
        with self.assertRaises(ValueError): inspect_raw(self.path, self.expected | {'layout':'cygno-5x5x3-v1'}, 2)
        with uproot.update(self.path) as f: del f['RunAccounting']
        with self.assertRaises(ValueError): inspect_raw(self.path, self.expected, 2)


class ProcessingTests(unittest.TestCase):
    def test_all_chunk_boundaries(self):
        rows = [{}, dict(VolumeNumber=1,EnergyDeposit=.002,x_hits=5), dict(VolumeNumber=0,x_hits=99),
                dict(ParticleName='alpha'), dict(ProcessType='eIoni',ParticleName='e+'),
                dict(ProcessType='phot'), dict(Nucleus='different'),
                dict(EventNumber=1,ParticleName='gamma'),dict(EventNumber=1,ProcessType='eIoni'),
                dict(EventNumber=1,ProcessType='eIoni',ParticleName='e+'),
                dict(EventNumber=1,ProcessType='eIoni',Nucleus='different'),
                dict(EventNumber=1,ProcessType='eIoni')]
        expected = list(groups([chunk(rows)]))
        self.assertEqual(len(expected), 4)
        self.assertEqual(expected[0].particle, 'alpha')  # inherited label, despite following e+
        self.assertEqual(list(expected[0].volumes), [0,1])
        self.assertEqual(expected[0].volumes[0].x, 0)  # first position retained
        self.assertEqual(expected[-1].particle, 'e+')
        for split in range(len(rows)+1):
            self.assertEqual(list(groups([chunk(rows[:split]),chunk(rows[split:])])), expected)
        self.assertEqual(list(groups([chunk([r]) for r in rows])), expected)
        self.assertEqual(list(groups([chunk([])])), [])

    def test_energy_and_cut(self):
        geometry = dict(gas_size_mm=[100,120,140],gas_centers_mm={'0':[5,6,7]})
        g = next(groups([chunk([dict(x_hits=35,y_hits=46,z_hits=57)])]))
        self.assertTrue(fiducial(g, geometry))
        g.volumes[0].x = math.nextafter(35, math.inf)
        self.assertFalse(fiducial(g, geometry))
        energies = [-1,0,10,math.nextafter(10,math.inf),400,math.nextafter(400,math.inf),1999,2000,2200]
        for e in energies:
            flags = window_flags(e)
            self.assertEqual(flags, (True,e>10,10<e<=400,e<0,0<=e<2000,e>=2000))
        rows=[dict(EventNumber=i,EnergyDeposit=e/1000) for i,e in enumerate([-1,0,10,11,400,401,1999,2000,2200])]
        counts,hist,n = accumulate(groups([chunk(rows)]),dict(gas_size_mm=[100]*3,gas_centers_mm={'0':[0]*3}))
        np.testing.assert_array_equal(counts[0], [9,6,2,1,6,2])
        self.assertEqual(int(hist[0].sum()), 9)
        self.assertEqual(n, 9)

    def test_normalization_categories(self):
        quantities = {'A':dict(mass_kg=2,pieces=7)}
        a = dict(id='a',component='A',activity=3,activity_unit='Bq/kg',category='GEMs')
        b = a | dict(id='b',activity_unit='Bq/piece')
        self.assertEqual(scale_for(a,quantities,31536000), 6)
        self.assertEqual(scale_for(b,quantities,31536000), 21)
        counts=np.ones((2,6),dtype=np.int64); h=np.ones((2,902),dtype=np.int64)
        spectra=summarize([(a,6,counts,h),(b,21,counts,h)])
        self.assertTrue(all(x['rate_per_year']==27 and x['variance_per_year2']==477 for x in spectra['categories']))


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'campaign'
        self.cfg,self.matrix,self.campaign=campaign_fixture(self.root)

    def populate(self, rows=None):
        with patch.object(rt,'invoke',side_effect=fake_invoke):
            for row in rows or self.matrix['contributions']:
                simulate.run_job(self.root,row,self.cfg,self.campaign,'fixture')
        simulate.update_campaign(self.root,self.campaign,self.matrix)

    def test_resume_corruption_mismatch(self):
        row=self.matrix['contributions'][0];self.populate([row])
        with patch.object(rt,'invoke',side_effect=AssertionError('must not rerun')):
            job=simulate.run_job(self.root,row,self.cfg,self.campaign,'fixture')
        self.assertEqual(job['attempt'],'attempt-0001')
        with self.assertRaises(ValueError): validate_campaign(self.root)
        self.assertEqual(len(validate_campaign(self.root,True)),1)
        with self.assertRaises(ValueError): package(self.root)
        with self.assertRaises(ValueError): simulate.run_job(self.root,row,self.cfg | {'seed':234},self.campaign,'fixture')
        raw=self.root/'jobs'/row['id']/job['attempt']/job['raw_path'];raw.write_bytes(b'corrupt')
        with self.assertRaises(ValueError): validate_campaign(self.root,True)

    def test_archive_and_analysis(self):
        self.populate()
        self.assertEqual(len(validate_campaign(self.root)),26)
        archive=package(self.root)
        self.assertTrue(archive.with_name(archive.name+'.sha256').exists())
        self.assertEqual(package(self.root),archive)
        with open_campaign(archive) as root:
            self.assertEqual(len(validate_campaign(root)),26)
            output=Path(self.tmp.name)/'analysis'
            self.assertEqual(analyze(root,output,step_size=1),0)
            for name in ['spectra.json','tables.json','table7.2.csv','table7.3.csv','figure7.5.png','figure7.5.pdf','figure7.6.png','figure7.6.pdf','analysis-manifest.json']:
                self.assertGreater((output/name).stat().st_size,0)
            self.assertEqual(rt.read(output/'analysis-manifest.json')['coverage'],'26/26')
            with self.assertRaises(ValueError): analyze(root,output)

    def test_partial_report_and_provenance(self):
        self.populate([self.matrix['contributions'][0]])
        output=Path(self.tmp.name)/'partial'
        with self.assertRaises(ValueError): analyze(self.root,output)
        self.assertEqual(analyze(self.root,output,allow_partial=True,step_size=1),2)
        report=rt.read(output/'analysis-manifest.json')
        self.assertFalse(report['complete_matrix']);self.assertEqual(report['coverage'],'1/26')
        self.assertIsNone(rt.read(output/'tables.json')['table7_3'][0]['calculated_counts_per_year'])
        campaign=rt.read(self.root/'campaign.json');campaign['identity']['config']['seed']=23
        rt.save(self.root/'campaign.json',campaign)
        with self.assertRaises(ValueError): validate_campaign(self.root,True)

    def test_unsafe_archives(self):
        for name,kind in [('../escape',tarfile.REGTYPE),('/absolute',tarfile.REGTYPE),
                          ('campaign/link',tarfile.SYMTYPE),('campaign/link',tarfile.LNKTYPE),
                          ('campaign/device',tarfile.CHRTYPE),('campaign/../escape',tarfile.REGTYPE)]:
            archive=Path(self.tmp.name)/'evil.tar.gz'
            with tarfile.open(archive,'w:gz') as tar:
                info=tarfile.TarInfo(name);info.type=kind;info.linkname='../outside';info.size=0
                tar.addfile(info,io.BytesIO(b''))
            with self.assertRaises(ValueError): extract(archive,Path(self.tmp.name)/'extract')

if __name__ == '__main__': unittest.main()

class CampaignIntegrityTests(unittest.TestCase):
    setUp = CampaignTests.setUp
    populate = CampaignTests.populate
    # Reuse fixture setup, without inheriting the slower report tests below.
    def test_failed_preflight(self):
        from study.campaign import validate_preflight
        path=self.root/self.campaign['preflight']
        preflight=rt.read(path);preflight['checks']['bi212-full']['status']='failed'
        rt.save(path,preflight)
        self.campaign['preflight_artifacts']=rt.artifacts(path.parent)
        with self.assertRaises(ValueError): validate_preflight(self.root,self.campaign)

    def test_archive_corruption_and_duplicate(self):
        from study.archive import archive_inventory
        self.populate()
        path=package(self.root)
        with tarfile.open(path,'r:gz') as original:
            entries=[(m,original.extractfile(m).read()) for m in original]
        damaged=Path(self.tmp.name)/'damaged.tar.gz'
        for duplicate in (False,True):
            with tarfile.open(damaged,'w:gz') as tar:
                for member,data in entries:
                    if not duplicate and member.name=='campaign/config.json': data=b'X'*len(data)
                    tar.addfile(member,io.BytesIO(data))
                if duplicate: tar.addfile(entries[0][0],io.BytesIO(entries[0][1]))
            with self.assertRaises(ValueError): archive_inventory(damaged)
            with self.assertRaises(ValueError):
                with open_campaign(damaged): pass
