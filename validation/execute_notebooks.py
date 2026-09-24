#!/usr/bin/env python3
"""Execute and save tutorial outputs without adding a notebook execution framework.

Jupyter users can execute normally. This helper handles these plain Python cells,
records stdout and embeds the common report PNGs; it does not interpret magics.
"""
import argparse
import hashlib
import base64
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO))


def execute(path, destination):
    notebook=json.loads(path.read_text())
    namespace={'__name__':'__notebook__'}
    count=0
    try:
        for cell in notebook['cells']:
            if cell['cell_type']!='code': continue
            count+=1
            source=''.join(cell['source'])
            stdout=io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exec(compile(source,str(path)+'#'+cell['id'],'exec'),namespace)
            cell['execution_count']=count
            text=stdout.getvalue()
            cell['outputs']=[dict(output_type='stream',name='stdout',text=text.splitlines(True))] if text else []
            cell['metadata']['scrolled']=True
            if 'render(OUTPUT_DIR' in source:
                for name in ('figure7.5.png','figure7.6.png'):
                    png=(namespace['OUTPUT_DIR']/name).read_bytes()
                    cell['outputs'].append(dict(output_type='display_data',metadata={},
                        data={'image/png':base64.b64encode(png).decode(),'text/plain':[name]}))
        sources = sorted((REPO/'analysis').rglob('*.py')) + [REPO/'study/analyze.py',
            REPO/'study/source_matrix.py', REPO/'study/requirements-analysis.txt']
        notebook['metadata']['cygno'] = dict(implementation_sha256={str(p.relative_to(REPO)):
            hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(json.dumps(notebook,indent=1,ensure_ascii=False)+'\n')
    finally:
        for name in ('example_directory','output_directory'):
            if name in namespace: namespace[name].cleanup()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True,help='Output directory mirroring analysis/ notebook paths')
    a=p.parse_args()
    for path in sorted((REPO/'analysis').rglob('*.ipynb')):
        execute(path,a.output/path.relative_to(REPO/'analysis'))
        print(path.relative_to(REPO))
