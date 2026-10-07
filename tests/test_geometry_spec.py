"""Independent assay/identity contracts; no Geant4 or ROOT required."""
import copy
import hashlib
import math
from pathlib import Path
import unittest
from study.source_matrix import read_matrix, validate_matrix, assay_activity, expected_contributions

REPO=Path(__file__).resolve().parents[1]

class AssaySpecificationTests(unittest.TestCase):
    def test_canonical_assays_and_historical_reference(self):
        old=REPO/'config/study/thesis-table7.1.json'
        matrix=read_matrix(REPO/'config/study/cygno-300elj-radioassay-v1.json')
        self.assertEqual(hashlib.sha256(old.read_bytes()).hexdigest(),
                         matrix['provenance']['retained_reference']['sha256'])
        self.assertEqual(len(expected_contributions()),31)
        self.assertEqual(len({r['category'] for r in matrix['contributions']}),7)
        self.assertAlmostEqual(assay_activity('U238',5.58),5.58e-9*12400)
        self.assertAlmostEqual(assay_activity('Th232',6.82),6.82e-9*4060)
        self.assertAlmostEqual(assay_activity('K40',108),.003294)
        self.assertAlmostEqual(assay_activity('K40',130),.003965)
        for material in ('GEMsPolyimide','GEMsCopper','CathodesPolyimide','CathodesCopper'):
            self.assertEqual({r['chain_start']['name'] for r in matrix['contributions'] if r['component']==material},
                             {'U238','Th232','K40'})
        # A reference table must never masquerade as a canonical production matrix.
        with self.assertRaises(ValueError):read_matrix(old)
        for field,value in [('matrix_id','thesis-table7.1-v1'),('seconds_per_year',31500000)]:
            bad=copy.deepcopy(matrix);bad[field]=value
            with self.assertRaises(ValueError):validate_matrix(bad)
        for field in ('activity','assay_material','activity_basis','component'):
            bad=copy.deepcopy(matrix);bad['contributions'][0][field]=1 if field=='activity' else 'wrong'
            with self.assertRaises(ValueError):validate_matrix(bad)
        bad=copy.deepcopy(matrix);bad['provenance']['specific_activities_Bq_g']['K40']=31.1
        with self.assertRaises(ValueError):validate_matrix(bad)

    def test_laminate_cross_check_and_constructed_fraction(self):
        # Independent per-material uncertainty check, documentation only;
        # production normalization does not propagate assay systematics.
        for poly,copper,whole,expected in [(5.58,12,8.6,10.3308),(6.82,12,20,10.6532),(108,130,164,124.28)]:
            self.assertAlmostEqual(.26*poly+.74*copper,expected)
        for delta,poly_error,copper_error,whole_error in [(10.3308-8.6,.16,13,3.6),(10.6532-20,.09,12,14),(124.28-164,38,180,82)]:
            combined=math.sqrt((.26*poly_error)**2+(.74*copper_error)**2+whole_error**2)
            self.assertLess(abs(delta)/combined,1)
        fraction=50*1.42/(50*1.42+10*8.96)
        self.assertAlmostEqual(fraction,.44209215442092153)
