"""Execute tutorial cells with existing analysis dependencies; no notebook framework."""
import contextlib
import io
import json
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
