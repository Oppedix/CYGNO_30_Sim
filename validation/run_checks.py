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
multithreaded=(build/'validation/multithreaded.txt').read_text().strip()=='ON'
suffix='_t0' if multithreaded else ''

def run(args, directory, log):
    with (directory/log).open('w') as out:
        result=subprocess.run([str(x) for x in args],cwd=directory,stdout=out,stderr=subprocess.STDOUT)
    if result.returncode: raise RuntimeError(f'{args[0]} failed: {directory/log}')
    return (directory/log).read_text()

def transport(case, directory, workers=1, macro=None, output_mode='raw'):
    directory.mkdir(parents=True,exist_ok=True)
    log=run([build/'rdecay01', macro or repo/'validation/macros'/f'{case}.mac',workers,'--output-mode',output_mode],directory,'run.log')
    assert 'COMMAND NOT FOUND' not in log and '***** Illegal' not in log and 'FatalException' not in log, directory
    return log

def check_identity(path,layout):
    import hashlib
    import ROOT
    f=ROOT.TFile.Open(str(path));metadata=f.Get('RunMetadata')
    assert metadata and metadata.GetEntries()==1,path
    metadata.GetEntry(0)
    for field,value in dict(Layout=layout,DetectorModel='code-compatible',SourcePolicy='historical',
                            GeometryHash=hashlib.sha256((repo/'common/DetectorGeometry.hh').read_bytes()).hexdigest()).items():
        assert metadata.GetLeaf(field).GetValueString()==value,(path,field)
    f.Close()

def accounting(path, requested, run_id=0):
    import ROOT
    f=ROOT.TFile.Open(str(path));tree=f.Get('RunAccounting')
    assert tree and tree.GetEntries()==1,path
    tree.GetEntry(0)
    fields=('RunID','RequestedEvents','GeneratedPrimaries','ProcessedEvents','AbortedEvents')
    assert all(tree.GetLeaf(name).GetTypeName()=='Int_t' for name in fields)
    values={name:int(tree.GetLeaf(name).GetValue()) for name in fields}
    assert values['RunID']==run_id and values['RequestedEvents']==requested,values
    assert values['AbortedEvents']==0 and values['GeneratedPrimaries']==values['ProcessedEvents'],values
    f.Close();return values['GeneratedPrimaries']

if mode=='geometry':
    out=root/'geometry'; out.mkdir(exist_ok=True)
    run([build/'validation/geometry_snapshot',out/'geometry.txt'],out,'snapshot.log')
    audit=run([build/'validation/geometry_audit',out/'placements.tsv','overlaps'],out,'audit.log')
    from check_geometry import check
    check(out/'placements.tsv',out/'placements.tsv',same_layout=True)
    assert len(re.findall(r'SOURCE_OK ',audit))==9
    print('Internal overlap warnings (diagnostic):',audit.count('GeomVol1002'))
elif mode=='layouts':
    from check_geometry import check
    from check_hits import check as check_hits
    from compare_hits import read_hits
    out=Path(tempfile.mkdtemp(prefix='layouts-',dir=root))
    profiles=('cygno-5x5x3-v1','legacy-25x3','cygno-11x7-v1')
    for profile in profiles:
        directory=out/profile; directory.mkdir()
        run([build/'validation/geometry_snapshot',directory/'geometry.txt',profile],directory,'snapshot.log')
        audit=run([build/'validation/geometry_audit',directory/'placements.tsv','overlaps','--layout',profile],directory,'audit.log')
        assert len(re.findall(r'SOURCE_OK ',audit))==9
        check(out/profiles[0]/'placements.tsv',directory/'placements.tsv',same_layout=True,profile=profile)
        # Verify the production JSON exporter against actual sensitive placements.
        run([build/'geometry_quantities',directory/'quantities.tsv',profile,directory/'geometry.json'],
            directory,'quantities.log')
        from check_geometry import read
        placed_gas={str(r['copy']):[r[a] for a in 'xyz'] for r in read(directory/'placements.tsv')
                    if r['sensitive']=='1'}
        exported=json.loads((directory/'geometry.json').read_text())
        assert exported['layout']==profile and exported['gas_centers_mm']==placed_gas
        assert exported['gas_size_mm']==[500,800,500]
        print(profile, 'inherited overlap warnings (diagnostic):',audit.count('GeomVol1002'))
        log=run([build/'rdecay01',repo/'validation/macros/smoke.mac','1','--layout',profile],directory,'smoke.log')
        assert f'CYGNO layout={profile} detector_model=code-compatible source_model=historical' in log
        assert 'The run was 20 Po212' in log and 'FatalException' not in log
        files=list((directory/'outfiles_V2').glob('*.root'))
        assert len(files)==1
        check_hits(str(directory/'placements.tsv'),20,[str(files[0])])
        check_identity(files[0],profile)
        if (build/'analysis/SimpleProcessEvents').exists():
            processed=directory/'processed.root'
            run([build/'analysis/SimpleProcessEvents',files[0],processed],directory,'process.log')
            import ROOT
            f=ROOT.TFile.Open(str(processed))
            assert f.Get('CygnoLayout').GetTitle()==profile
            assert f.Get('CygnoDetectorModel').GetTitle()=='code-compatible'
            assert f.Get('RunMetadata').GetEntries()==1
            f.Close()
    # Compare an explicit current-profile run with the backward-compatible default.
    directory=out/'default'; directory.mkdir()
    run([build/'rdecay01',repo/'validation/macros/smoke.mac'],directory,'smoke.log')
    raw=f'outfiles_V2/cleanup_smoke{suffix}.root'
    assert read_hits(directory/raw)==read_hits(out/profiles[0]/raw)
    # Misspellings/malformed options must never launch a different layout/job.
    for args in [ ['--layout','25x3'], ['--layout'], ['--unknown'],
                  ['--layout',profiles[0],'--layout',profiles[1]],
                  ['missing.mac','0'], ['missing.mac','2junk'], ['a','b','c'] ]:
        result=subprocess.run([str(build/'rdecay01'),*args],cwd=directory,capture_output=True,text=True)
        assert result.returncode!=0 and 'Use --help' in result.stderr, args
    print('PASS: all three geometry profiles, local internals, source lists, CLI and smoke transport;',out)
elif mode=='transport':
    from check_hits import check
    out=Path(tempfile.mkdtemp(prefix='transport-',dir=root))
    run([build/'validation/geometry_audit',out/'placements.tsv'],out,'audit.log')
    results={}
    for case,events,workers in [('smoke',20,1),('chain',40,1),('partial_chain',40,1),('stop_chain',40,1),('threads',40,2)]:
        if workers>1 and not multithreaded:
            print('SKIP: multi-worker case requires a multithreaded Geant4 build')
            continue
        directory=out/case
        log=transport('chain' if case=='threads' else case,directory,workers)
        primary='Po212' if case=='smoke' else 'Bi211'
        assert f'The run was {events} {primary}' in log, case
        if case=='chain': assert re.search(r'Pb207\s*:',log)
        if case in ('partial_chain','stop_chain'): assert not re.search(r'Pb207\s*:',log)
        files=sorted((directory/'outfiles_V2').glob('*.root'))
        assert len(files)==workers,(case,files)
        check(str(out/'placements.tsv'),events,[str(p) for p in files])
        for path in files: check_identity(path,'cygno-5x5x3-v1')
        assert sum(accounting(path,events) for path in files)==events
        from compare_hits import read_hits
        results[case]={p.name:len(read_hits(p)[1]) for p in files}
    # Each output mode must reset rows, group indices, tracks and accounting
    # between runs. Use production pure readers with PyROOT-extracted records:
    # these CTest checks still need no uproot/numpy installation.
    import ROOT
    sys.path.insert(0,str(repo))
    from analysis.compact.io import SCHEMAS
    from analysis.compact.preprocess import reconstruct
    from analysis.raw.preprocess import groups
    from analysis.common.io import TIMING_DEFINITION, PROCESSING_VERSION

    def records(tree):
        leaves=list(tree.GetListOfLeaves())
        result=[]
        for entry in range(tree.GetEntries()):
            tree.GetEntry(entry)
            result.append({leaf.GetName(): leaf.GetValueString() if leaf.GetTypeName()=='Char_t'
                else int(leaf.GetValue()) if leaf.GetTypeName()=='Int_t' else leaf.GetValue()
                for leaf in leaves})
        return result

    def raw_groups(path):
        file=ROOT.TFile.Open(str(path))
        rows=records(file.Get('Hits'));file.Close()
        tracks=[]
        canonical=list(groups([{key:[row[key] for row in rows] for key in rows[0]}],tracks.append)) if rows else []
        return canonical,tracks

    baseline=out/f'smoke/outfiles_V2/cleanup_smoke{suffix}.root'
    baseline_groups,baseline_tracks=raw_groups(baseline)
    for output_mode in ('raw','compact','both'):
        multi=out/('multi-'+output_mode);multi.mkdir()
        text=(repo/'validation/macros/smoke.mac').read_text()
        macro=multi/'multi.mac'
        macro.write_text(text.replace('cleanup_smoke','first')+
            '\n/random/setSeeds 12345 67890\n/output/OutFile second\n/run/beamOn 10\n')
        transport('smoke',multi,macro=macro,output_mode=output_mode)
        for name in ('first','second'):
            path=multi/'outfiles_V2'/f'{name}{suffix}.root'
            requested=20 if name=='first' else 10
            file=ROOT.TFile.Open(str(path))
            expected={'RunMetadata','RunAccounting','OutputMetadata'}
            if output_mode!='compact': expected.add('Hits')
            if output_mode!='raw': expected.update(SCHEMAS)
            keys=[key.GetName() for key in file.GetListOfKeys()]
            assert len(keys)==len(expected) and set(keys)==expected,(output_mode,keys)
            metadata=records(file.Get('OutputMetadata'))
            assert metadata==[dict(OutputFormat=output_mode,OutputSchemaVersion=1,
                TimingDefinition=TIMING_DEFINITION,CompactProcessingVersion=PROCESSING_VERSION)]
            check_identity(path,'cygno-5x5x3-v1')
            assert accounting(path,requested,0 if name=='first' else 1)==requested
            if output_mode!='raw':
                data={key:records(file.Get(key)) for key in SCHEMAS}
                for tree,rows in data.items():
                    assert all(0<=row['EventNumber']<requested for row in rows),(tree,name)
                    assert [r['EventNumber'] for r in rows]==sorted(r['EventNumber'] for r in rows)
                canonical,tracks=[],[]
                for event in range(requested):
                    g,t=reconstruct(event,{key:[r for r in rows if r['EventNumber']==event]
                                           for key,rows in data.items()},'cygno-5x5x3-v1')
                    canonical.extend(g);tracks.extend(t)
                if name=='first':
                    assert canonical==baseline_groups and tracks==baseline_tracks
                if output_mode=='both':
                    assert (canonical,tracks)==raw_groups(path)
            file.Close()
            if output_mode!='compact':
                check(str(out/'placements.tsv'),requested,[str(path)])
                if name=='first': assert read_hits(path)==read_hits(baseline)
        results['multiple_runs_'+output_mode]='first matches fresh transport; second has reset rows, event/group/track keys and accounting'
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
