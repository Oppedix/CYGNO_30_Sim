"""Compile/run every active reference ROOT analyzer without a Geant4 build.

Synthetic inputs/quantities only; these checks make no transport/rate prediction.
Run alongside test_topology.py and test_external.py in each supported ROOT version.
"""
import math
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest
import numpy as np
import uproot
from analysis.common.spectra import accumulate, fiducial, group_energy
from analysis.raw.io import header, hit_chunks
from analysis.raw.preprocess import groups
from study import runtime as rt
from fixtures import raw_fixture, campaign_fixture


@unittest.skipUnless(shutil.which('root-config'), 'ROOT required for reference compatibility')
class ReferenceRootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.root=Path(cls.tmp.name)
        # Reference programs require build identity, but not Geant4 or simulation code.
        template=(rt.REPO/'common/BuildInfo.hh.in').read_text()
        for name,value in dict(CYGNO_SOURCE_HASH='synthetic-root-compatibility-test',
                               CYGNO_GEOMETRY_HASH=rt.digest(rt.REPO/'common/DetectorGeometry.hh'),
                               CYGNO_EXTERNAL_GEOMETRY_HASH=rt.digest(rt.REPO/'common/ExternalGeometry.hh')).items():
            template=template.replace('@'+name+'@',value)
        (cls.root/'BuildInfo.hh').write_text(template)
        flags=shlex.split(subprocess.check_output(['root-config','--cflags','--libs'],text=True))
        source=rt.REPO/'analysis/reference_cpp'
        cls.plotters=('PlotNormalizedSpectra','PlotNormalizedSpectra_single','PlotNormalizedSpectra_GEMchain')
        for name in ('SimpleProcessEvents',*cls.plotters):
            files=[source/(name+'.cpp')]
            if name=='SimpleProcessEvents':files.append(source/'ProcessEvents.cc')
            subprocess.run(['c++','-O2','-std=c++17','-ffp-contract=off','-I'+str(cls.root),
                            *map(str,files),*flags,'-o',str(cls.root/name)],check=True,capture_output=True)
        macro=cls.root/'macro.cpp'
        macro.write_text('#include <TROOT.h>\n#include "'+str(source/'PlotSpectrum.C')+'"\n'
                         'int main(int argc,char**argv){gROOT->SetBatch(true);'
                         'try{PlotSpectra(argv[1]);return 0;}'
                         'catch(const std::exception& e){std::cerr<<e.what();return 1;}}\n')
        subprocess.run(['c++','-O2','-std=c++17','-ffp-contract=off','-I'+str(cls.root),
                        str(macro),*flags,'-o',str(cls.root/'PlotSpectrum')],check=True,capture_output=True)

    def test_all_reference_programs_material_and_gas_normalization(self):
        for gas in (False,True):
            with self.subTest(gas=gas):
                folder=self.root/str(gas);folder.mkdir()
                config,matrix,campaign=campaign_fixture(folder/'campaign','cygno-copper-cathode-v4',gas)
                expected=dict(layout='legacy-25x3',model=config['model'],source_policy=config['source_policy'],
                              geometry_hash=rt.digest(rt.REPO/'common/DetectorGeometry.hh'))
                # Module 0 of the legacy layout; fiducial and just-outside positions.
                center=[-6048.,-804.,250.03]
                energies=[-1.,0.,10.,math.nextafter(10.,math.inf),400.,math.nextafter(400.,math.inf),2000.,2200.]
                for nbins in (900,1200):
                    for i in range(1,nbins):
                        edge=i*(2000./nbins)
                        energies.extend([math.nextafter(edge,-math.inf),edge,math.nextafter(edge,math.inf)])
                rows=[dict(EventNumber=i,EnergyDeposit=e/1000,x_hits=center[0],y_hits=center[1],z_hits=center[2])
                      for i,e in enumerate(energies)]
                rows.append(dict(EventNumber=len(rows),EnergyDeposit=.02,x_hits=center[0]+231,
                                 y_hits=center[1],z_hits=center[2]))
                raw=folder/'raw.root';processed=folder/'processed.root'
                raw_fixture(raw,expected,rows,requested=len(rows))
                subprocess.run([self.root/'SimpleProcessEvents',raw,processed],check=True,capture_output=True)
                geom=dict(gas_centers_mm={'0':center},gas_size_mm=[500.,800.,500.])
                with uproot.open(raw) as file:
                    _,tree=header(file,expected,len(rows))
                    canonical=list(groups(hit_chunks(tree,len(rows),'legacy-25x3')))
                counts,bins,_=accumulate(canonical,geom)
                reference_bins={900:bins,1200:np.zeros((2,1202),dtype=np.int64)}
                moments=np.zeros((2,4))
                for group in canonical:
                    energy=group_energy(group)
                    width=2000./1200
                    approximate=int(energy/width)
                    index=0 if energy<0 else 1201 if energy>=2000 else (
                        1+approximate-int(energy<width*approximate)+int(width*(approximate+1)<=energy))
                    for cut in range(2 if fiducial(group,geom) else 1):
                        reference_bins[1200][cut,index]+=1
                        if 0<=energy<2000:moments[cut]+=[1.,1.,energy,energy*energy]
                with uproot.open(processed) as file:
                    self.assertEqual(file['elabHits'].num_entries,len(canonical))
                    self.assertEqual(file['CygnoDetectorModel'].member('fTitle'),config['model'])
                lines=['# normalization-format: quantity-v2','# layout: legacy-25x3',
                       '# detector-model: '+config['model'],'# source-policy: uniform-volume-v1',
                       '# provenance: synthetic ROOT compatibility regression']
                scales={}
                for row in matrix['contributions']:
                    quantity=campaign['quantities'][row['component']]['mass_kg' if row['activity_unit']=='Bq/kg' else 'pieces']
                    unit='kg' if row['activity_unit']=='Bq/kg' else 'piece'
                    scales[row['id']]=row['activity']*quantity*60*60*24*365/len(rows)
                    lines.append(f'{row["component"]} {row["chain_start"]["name"]} {quantity:.17g} {unit} '
                                 f'{row["activity"]:.17g} {row["activity_unit"]} {len(rows)} "{row["category"]}" "{processed}"')
                normalization=folder/'normalization.tsv';normalization.write_text('\n'.join(lines)+'\n')
                for program in self.plotters:
                    output=folder/program;output.mkdir()
                    subprocess.run([self.root/program,normalization],cwd=output,check=True,capture_output=True)
                    with uproot.open(output/'NormalizedHisto.root') as file:
                        categories={}
                        for row in matrix['contributions']:
                            scale=scales[row['id']]
                            for cut in (0,1):
                                h=file[row['id']+('_cut' if cut else '')]
                                self.assertAlmostEqual(h.values(flow=True).sum(),counts[cut,0]*scale,
                                                       delta=max(1e-15,abs(counts[cut,0]*scale)*1e-14))
                                expected_bins=reference_bins[len(h.values())][cut]
                                self.assertEqual(h.member('fEntries'),counts[cut,0])
                                np.testing.assert_allclose(h.values(flow=True),expected_bins*scale,rtol=1e-14,atol=0)
                                np.testing.assert_allclose(h.variances(flow=True),expected_bins*scale*scale,rtol=1e-14,atol=0)
                                stats=[h.member(name) for name in ('fTsumw','fTsumw2','fTsumwx','fTsumwx2')]
                                np.testing.assert_allclose(stats,moments[cut]*[scale,scale*scale,scale,scale],rtol=1e-14)
                                key=row['category']+('_cut' if cut else '')
                                categories.setdefault(key,np.zeros_like(expected_bins,dtype=float))[:]+=expected_bins*scale
                        for category,expected_bins in categories.items():
                            np.testing.assert_allclose(file['Categories/'+category].values(flow=True),expected_bins,rtol=1e-14,atol=0)
                        for category in ('Gas C14','Gas Rn222') if gas else ('Cathodes',):
                            self.assertIn('Categories/'+category,file)
                        self.assertIn('NormalizationConfiguration',file)
                subprocess.run([self.root/'PlotSpectrum',processed],check=True,capture_output=True)
                with uproot.open(folder/'histo_processed.root') as file:
                    # This macro fills per-volume electron spectra; all test groups have one volume.
                    for cut in (0,1):
                        np.testing.assert_array_equal(file['betaplot'+('_cut' if cut else '')].values(flow=True),bins[cut])
                        stats=[file['betaplot'+('_cut' if cut else '')].member(name)
                               for name in ('fTsumw','fTsumw2','fTsumwx','fTsumwx2')]
                        np.testing.assert_allclose(stats,moments[cut],rtol=1e-14)


if __name__=='__main__':unittest.main()
