"""Execute tutorial cells with existing analysis dependencies; no notebook framework."""
import contextlib
import io
import json
import os
from pathlib import Path
import unittest
from study.runtime import REPO, digest

class NotebookTests(unittest.TestCase):
    def test_walkthroughs(self):
        for path in sorted((REPO/'analysis').rglob('*.ipynb')):
            with self.subTest(notebook=path.name):
                notebook=json.loads(path.read_text())
                self.assertEqual(notebook['nbformat'],4)
                recorded=notebook['metadata']['cygno']['implementation_sha256']
                sources = sorted((REPO/'analysis').rglob('*.py')) + [REPO/'study/analyze.py',
                    REPO/'study/source_matrix.py', REPO/'study/requirements-analysis.txt']
                self.assertEqual(recorded,{str(p.relative_to(REPO)):digest(p) for p in sources},
                    'Production changed: refresh saved tutorial outputs with validation/execute_notebooks.py')
                namespace={'__name__':'__notebook__'}
                ids=set()
                with contextlib.redirect_stdout(io.StringIO()):
                    for cell in notebook['cells']:
                        self.assertNotIn(cell['id'],ids);ids.add(cell['id'])
                        source=''.join(cell['source'])
                        if cell['cell_type']=='code':
                            self.assertTrue(all(o['output_type'] in ('stream','display_data') for o in cell['outputs']))
                            exec(compile(source,str(path)+'#'+cell['id'],'exec'),namespace)
                    # Keep the repository clean; optional Jupyter display uses the live temporary files.
                    for name in ('example_directory','output_directory'):
                        if name in namespace: namespace[name].cleanup()

class ConstructedCampaignNotebookTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('CYGNO_REFERENCE_BUILD'),
                         'Set CYGNO_REFERENCE_BUILD for constructed 11x7 campaign walkthrough')
    def test_11x7_real_campaign_path(self):
        """Real exporter/analysis, synthetic events and preflight; no physics claim."""
        import subprocess
        import tempfile
        from unittest.mock import patch
        import numpy as np
        from study import runtime as rt, simulate
        from study.source_matrix import read_quantities
        from study.analyze import analyze
        from analysis.common.spectra import scale_for
        from fixtures import campaign_fixture, log_for
        from compact_fixtures import fixture
        build=Path(os.environ['CYGNO_REFERENCE_BUILD']).resolve()
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            root=Path(temporary)/'campaign'
            cfg,matrix,campaign=campaign_fixture(root)
            cfg.update(layout='cygno-11x7-v1',output_mode='both',output_schema_version=1)
            subprocess.run([build/'geometry_quantities',root/'quantities.tsv',cfg['layout'],root/'geometry.json'],
                           check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            geometry=rt.read(root/'geometry.json')
            self.assertEqual(set(geometry['gas_centers_mm']),{str(i) for i in range(154)})
            self.assertEqual(geometry['gas_centers_mm']['153'],[2520,2412,-250.25])
            env=campaign['identity']['effective_environment']
            env.update(source_hash=geometry['source_hash'],geometry_hash=geometry['geometry_hash'])
            quantities=read_quantities(root/'quantities.tsv',layout=cfg['layout'],model=cfg['model'],
                                      geometry_hash=env['geometry_hash'])
            self.assertEqual({k:v['pieces'] for k,v in quantities.items()},dict(Cathodes=77,GEMsOuter=462,
                GEMsCore=462,RingSupports=154,RingStrips=616,Resistors=770,Lens=308,Sensors=308,Vessel=1))
            self.assertTrue(all(v['mass_kg']>0 for v in quantities.values()))
            campaign.update(schema_version=3,quantities=quantities,fingerprint=rt.object_digest(campaign['identity']))
            rt.save(root/'config.json',cfg)
            preflight_path=root/'preflight/preflight.json'
            preflight=rt.read(preflight_path)
            for check in preflight['checks'].values(): check['environment']=env
            rt.save(preflight_path,preflight)
            campaign['preflight_artifacts']=rt.artifacts(preflight_path.parent)
            campaign['snapshots']={name:rt.digest(root/name) for name in campaign['snapshots']}
            rt.save(root/'campaign.json',campaign)
            expected={k:cfg[k] for k in ('layout','model','source_policy')} | dict(geometry_hash=env['geometry_hash'])
            center=geometry['gas_centers_mm']['153']
            records=[dict(VolumeNumber=153,x_hits=center[0]+offset,y_hits=center[1],z_hits=center[2],
                          EnergyDeposit=.02,EventNumber=event) for event,offset in enumerate((230,231))]
            def invoke(command,cwd,label,timeout,**options):
                fixture(cwd/'outfiles_V2/both.root',expected,records=records,requested=2)
                log=log_for(env,2);(cwd/(label+'.log')).write_text(log)
                rt.save(cwd/(label+'.command.json'),dict(command=list(map(str,command)),returncode=0))
                return log
            with patch.object(rt,'invoke',side_effect=invoke):
                for row in matrix['contributions']: simulate.run_job(root,row,cfg,campaign,'synthetic')
            simulate.update_campaign(root,campaign,matrix)
            output=Path(temporary)/'analysis'
            self.assertEqual(analyze(root,output),0)
            self.assertEqual(rt.read(output/'analysis-manifest.json')['normalized_parity']['status'],'passed')
            notebook=json.loads((REPO/'analysis/common/CYGNO30_background_analysis_walkthrough.ipynb').read_text())
            namespace={'__name__':'__notebook__'}
            try:
                for cell in notebook['cells']:
                    if cell['cell_type']!='code': continue
                    source=''.join(cell['source'])
                    # Set the documented input without changing the saved teaching fixture.
                    source=source.replace('CAMPAIGN_DIR = None',f'CAMPAIGN_DIR = {str(root)!r}')
                    exec(compile(source,'11x7-campaign-walkthrough','exec'),namespace)
                self.assertEqual(namespace['geometry'],geometry)
                self.assertEqual(namespace['quantities'],quantities)
                self.assertEqual(namespace['spectra'],rt.read(output/'spectra.json'))
                for row,scale,counts,histogram in namespace['results']:
                    self.assertEqual(scale,scale_for(row,quantities,2))
                    np.testing.assert_array_equal(counts[:,0],[2,1])
                for name in ('tables.json','table7.2.csv','table7.3.csv','figure7.5.png','figure7.6.png'):
                    self.assertGreater((namespace['OUTPUT_DIR']/name).stat().st_size,0)
            finally:
                if 'output_directory' in namespace: namespace['output_directory'].cleanup()
