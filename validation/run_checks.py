#!/usr/bin/env python3
"""Fresh isolated runs. Requires configured Geant4 datasets and PyROOT for transport.

The bi212 mode is deliberately separate from CTest's passing suite.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
repo=Path(__file__).resolve().parents[1]
mode=sys.argv[1]; build=Path(sys.argv[2]).resolve()
root=build/'validation-results'; root.mkdir(exist_ok=True)

def run(args, directory, log):
    with (directory/log).open('w') as out:
        result=subprocess.run([str(x) for x in args],cwd=directory,stdout=out,stderr=subprocess.STDOUT)
    if result.returncode: raise RuntimeError(f'{args[0]} failed: {directory/log}')
    return (directory/log).read_text()

def transport(case, directory, workers=1, macro=None):
    directory.mkdir(parents=True,exist_ok=True)
    log=run([build/'rdecay01', macro or repo/'validation/macros'/f'{case}.mac',workers],directory,'run.log')
    assert 'COMMAND NOT FOUND' not in log and '***** Illegal' not in log and 'FatalException' not in log, directory
    return log

if mode=='geometry':
    out=root/'geometry'; out.mkdir(exist_ok=True)
    run([build/'validation/geometry_snapshot',out/'geometry.txt'],out,'snapshot.log')
    audit=run([build/'validation/geometry_audit',out/'placements.tsv','overlaps'],out,'audit.log')
    from check_geometry import check
    check(out/'placements.tsv',out/'placements.tsv',same_layout=True)
    assert len(re.findall(r'SOURCE_OK ',audit))==9
    print('Internal overlap warnings (diagnostic):',audit.count('GeomVol1002'))
elif mode=='transport':
    from check_hits import check
    out=Path(tempfile.mkdtemp(prefix='transport-',dir=root))
    run([build/'validation/geometry_audit',out/'placements.tsv'],out,'audit.log')
    results={}
    for case,events,workers in [('smoke',20,1),('chain',40,1),('partial_chain',40,1),('stop_chain',40,1),('threads',40,2)]:
        directory=out/case
        log=transport('chain' if case=='threads' else case,directory,workers)
        primary='Po212' if case=='smoke' else 'Bi211'
        assert f'The run was {events} {primary}' in log, case
        if case=='chain': assert re.search(r'Pb207\s*:',log)
        if case in ('partial_chain','stop_chain'): assert not re.search(r'Pb207\s*:',log)
        files=sorted((directory/'outfiles_V2').glob('*.root'))
        assert len(files)==workers,(case,files)
        check(str(out/'placements.tsv'),events,[str(p) for p in files])
        from compare_hits import read_hits
        results[case]={p.name:len(read_hits(p)[1]) for p in files}
    # Same seeds and separate filenames in two runs: no extra ntuples, stale rows,
    # or reset event IDs leaking into the next run's tree.
    multi=out/'multi';multi.mkdir()
    text=(repo/'validation/macros/smoke.mac').read_text()
    macro=multi/'multi.mac'
    macro.write_text(text.replace('cleanup_smoke','first')+'\n/random/setSeeds 12345 67890\n/output/OutFile second\n/run/beamOn 10\n')
    log=transport('smoke',multi,macro=macro)
    import ROOT
    for name in ('first','second'):
        f=ROOT.TFile.Open(str(multi/'outfiles_V2'/f'{name}_t0.root'))
        assert [k.GetName() for k in f.GetListOfKeys()]==['Hits']
        f.Close()
        check(str(out/"placements.tsv"),20 if name=="first" else 10,[str(multi/"outfiles_V2"/f"{name}_t0.root")])
        if name=="first": assert read_hits(multi/"outfiles_V2"/f"{name}_t0.root")==read_hits(out/"smoke/outfiles_V2/cleanup_smoke_t0.root")
    results['multiple_runs']='first run exactly matches fresh process; both have one valid Hits tree with reset event IDs; solid RNG continues across runs'
    (out/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
elif mode=='bi212':
    out=Path(tempfile.mkdtemp(prefix='bi212-',dir=root))
    with (out/'run.log').open('w') as log:
        result=subprocess.run([str(build/'rdecay01'),str(repo/'validation/macros/known_bi212_failure.mac')],cwd=out,stdout=log,stderr=subprocess.STDOUT)
    text=(out/'run.log').read_text()
    if result.returncode and 'PART122' in text and 'Pb208' in text:
        print('EXPECTED KNOWN FAILURE: Bi212/Pb208 PART122;',out/'run.log')
    else: raise RuntimeError(f'Reproducer changed (exit {result.returncode}); inspect {out}/run.log')
else: raise ValueError(mode)
