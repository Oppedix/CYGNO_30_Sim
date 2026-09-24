"""Optional real C++ reference comparison. Set CYGNO_REFERENCE_BUILD to enable."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import numpy as np
import uproot
from study import runtime as rt
from analysis.raw.preprocess import groups
from analysis.raw.io import header, hit_chunks
from analysis.common.spectra import accumulate, scale_for, WINDOWS
from study.source_matrix import read_matrix, read_quantities
from fixtures import raw_fixture


@unittest.skipUnless(os.environ.get('CYGNO_REFERENCE_BUILD'), 'Set CYGNO_REFERENCE_BUILD for optional C++/ROOT parity')
class ReferenceParity(unittest.TestCase):
    def test_all_layouts(self):
        build=Path(os.environ['CYGNO_REFERENCE_BUILD']).resolve()
        for layout in ('legacy-25x3','cygno-5x5x3-v1','cygno-11x7-v1'):
            with self.subTest(layout=layout), tempfile.TemporaryDirectory() as d:
                folder=Path(d)
                subprocess.run([build/'geometry_quantities', folder/'quantities.tsv',layout,folder/'geometry.json'],
                    check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                geometry=rt.read(folder/'geometry.json')
                expected=dict(layout=layout,model='code-compatible',source_policy='historical',geometry_hash=geometry['geometry_hash'])
                center=geometry['gas_centers_mm']['0']
                def row(**kw):
                    return dict(x_hits=center[0],y_hits=center[1],z_hits=center[2]) | kw
                rows=[row(),row(VolumeNumber=1,EnergyDeposit=.002),row(ParticleName='alpha'),
                      row(ProcessType='eIoni',ParticleName='e+'),row(ProcessType='phot'),
                      row(EventNumber=1,ParticleName='gamma'),row(EventNumber=1,ProcessType='ionIoni'),
                      row(EventNumber=1,ProcessType='ionIoni',ParticleName='e+'),
                      row(EventNumber=1,Nucleus='different',ProcessType='ionIoni'),row(EventNumber=1)]
                energies=[-1.,0.,10.,10.0000001,400.,400.000001,1999.,2000.,2200.]
                # Include every histogram edge and nearby values to expose binning differences.
                for edge in np.linspace(0,2000,901):
                    energies.extend([float(edge), float(np.nextafter(edge,-np.inf)),float(np.nextafter(edge,np.inf))])
                for i,energy in enumerate(energies,2):
                    rows.append(row(EventNumber=i,EnergyDeposit=energy/1000))
                rows.append(row(EventNumber=len(energies)+2,EnergyDeposit=.02,
                    x_hits=center[0]+geometry['gas_size_mm'][0]/2-20))
                rows.append(row(EventNumber=len(energies)+3,EnergyDeposit=.02,
                    x_hits=center[0]+geometry['gas_size_mm'][0]/2-20+.01))
                # Unique diagnostic identities for synthetic tracks; grouping never uses IDs.
                for track_id, record in enumerate(rows, 1):
                    record['ParticleID'] = track_id
                    record['ParticleTag'] = {'e-':0,'e+':1,'gamma':2,'alpha':3}.get(record.get('ParticleName','e-'),-1)
                from compact_fixtures import fixture
                from analysis.compact.parity import validate
                both=folder/'both.root'
                fixture(both,expected,records=rows,requested=len(energies)+4)
                with uproot.open(both) as f:
                    validate(f,expected,len(energies)+4,geometry,step_size=3)
                raw=folder/'raw.root';processed=folder/'processed.root'
                raw_fixture(raw,expected,rows,requested=len(energies)+4)
                subprocess.run([build/'analysis/SimpleProcessEvents',raw,processed],check=True,stdout=subprocess.DEVNULL)
                with uproot.open(raw) as f:
                    _,hits=header(f,expected,len(energies)+4)
                    py=list(groups(hit_chunks(hits,len(energies)+4,layout,step_size=3)))
                with uproot.open(processed) as f:
                    cpp=f['elabHits'].arrays(library='ak')
                    self.assertEqual(len(cpp),len(py))
                    for c,p in zip(cpp,py):
                        self.assertEqual((c.evNumber,c.PartName,c.Nucleus),(p.event,p.particle,p.nucleus))
                        self.assertEqual(list(c.VolNnum_Out),list(p.volumes))
                        for index,field in enumerate(('EDep_Out','X_Vertex','Y_Vertex','Z_Vertex')):
                            np.testing.assert_array_equal(list(c[field]),[getattr(v, ("energy","x","y","z")[index]) for v in p.volumes.values()])
                counts,hist,_=accumulate(py,geometry)
                matrix=read_matrix(rt.REPO/'config/study/thesis-table7.1.json')
                quantities=read_quantities(folder/'quantities.tsv',layout=layout,model='code-compatible',geometry_hash=geometry['geometry_hash'])
                lines=['# normalization-format: quantity-v2',f'# layout: {layout}', '# detector-model: code-compatible',
                       '# source-policy: historical','# provenance: synthetic parity; not simulated backgrounds']
                category_hist={}
                from study.source_matrix import quantity_for
                for contribution in matrix['contributions']:
                    quantity=quantity_for(contribution,quantities)
                    unit='piece' if contribution['activity_unit']=='Bq/piece' else 'kg'
                    lines.append(f'{contribution["component"]} {contribution["chain_start"]["name"]} {quantity:.17g} {unit} {contribution["activity"]:.17g} {contribution["activity_unit"]} {len(energies)+4} "{contribution["category"]}" "{processed}"')
                (folder/'norm.tsv').write_text('\n'.join(lines)+'\n')
                subprocess.run([build/'analysis/PlotNormalizedSpectra',folder/'norm.tsv'],cwd=folder,check=True,stdout=subprocess.DEVNULL)
                with uproot.open(folder/'NormalizedHisto.root') as f:
                    windows=f['ExactEnergyWindows'].arrays(library='np')
                    scales={r['id']:scale_for(r,quantities,len(energies)+4) for r in matrix['contributions']}
                    for c in matrix['contributions']:
                        scale=scales[c['id']]
                        for cut in (0,1):
                            h=f[c['id']+('_cut' if cut else '')]
                            np.testing.assert_allclose(h.values(flow=True),hist[cut]*scale,rtol=1e-14,atol=0)
                            np.testing.assert_allclose(h.variances(flow=True),hist[cut]*scale*scale,rtol=1e-14,atol=0)
                            category_hist.setdefault((c['category'],cut),np.zeros(902))[:] += hist[cut]*scale
                    for i in range(len(windows['Count'])):
                        count=counts[windows['Fiducial'][i],WINDOWS.index(windows['Window'][i])]
                        self.assertEqual(windows['Count'][i],count)
                        scale=scales[windows['Contribution'][i]]
                        self.assertAlmostEqual(windows['RatePerYear'][i],count*scale,delta=max(1e-12,abs(count*scale)*1e-14))
                    for (category,cut),histogram in category_hist.items():
                        np.testing.assert_allclose(f['Categories/'+category+('_cut' if cut else '')].values(flow=True),histogram,rtol=1e-14)

if __name__ == '__main__': unittest.main()
