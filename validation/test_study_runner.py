#!/usr/bin/env python3
"""Synthetic runner success/failure/resume plus exact unbinned window boundaries.

Only the environment probe/quantity export construct Geant4; no matrix transport.
Real processing/plotting read hand-made ROOT files. Transport is checked separately.
"""
import argparse
import array
import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch
import ROOT
from check_hits import SCHEMA
ROOT.gROOT.SetBatch(True)
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))
from study import runner
from study.root_io import inspect_raw, export_spectra
from study.source_matrix import read_matrix
build = Path(sys.argv[1]).resolve()
out = Path(tempfile.mkdtemp(prefix='study-runner-', dir=build/'validation-results'))
config = runner.load_config(repo/'config/study/smoke-A.json')
matrix = read_matrix(repo/'config/study/thesis-table7.1.json')
identity = dict(layout=config['layout'], model='code-compatible', source_policy='historical',
                geometry_hash=runner.digest(repo/'common/DetectorGeometry.hh'))


def rejects(call):
    try:
        call()
    except (ValueError, RuntimeError, OSError):
        return
    raise AssertionError('Expected rejection')


def raw_fixture(path, *, accounting=True, generated=2, processed=2, aborted=0, hit=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    file = ROOT.TFile(str(path), 'RECREATE')
    hits = ROOT.TTree('Hits', 'synthetic Hits')
    buffers = {}
    for name, kind in SCHEMA:
        buffers[name] = array.array('b', [0]*256) if kind == 'Char_t' else array.array('i' if kind == 'Int_t' else 'd', [0])
        hits.Branch(name, buffers[name], name+'/'+{'Char_t': 'C', 'Int_t': 'I', 'Double_t': 'D'}[kind])
    if hit:
        values = dict(EventNumber=0, ParticleName='e-', ParticleID=1, ParticleTag=0,
                      ParentID=0, x_hits=0., y_hits=0., z_hits=250.25,
                      EnergyDeposit=.0101, VolumeNumber=37, Nucleus='fixture', ProcessType='RadioactiveDecay')
        for name, value in values.items():
            if isinstance(value, str):
                buffers[name][:] = array.array('b', value.encode()+bytes(256-len(value)))
            else:
                buffers[name][0] = value
        hits.Fill()
    hits.Write()
    metadata = ROOT.TTree('RunMetadata', 'identity')
    fields = {}
    for name, value in dict(GeometryHash=identity['geometry_hash'], Layout=identity['layout'],
                            DetectorModel=identity['model'], SourcePolicy=identity['source_policy']).items():
        fields[name] = array.array('b', value.encode()+b'\0')
        metadata.Branch(name, fields[name], name+'/C')
    metadata.Fill(); metadata.Write()
    if accounting:
        tree = ROOT.TTree('RunAccounting', 'synthetic accounting')
        numbers = {name: array.array('i', [value]) for name, value in
                   dict(RunID=0, RequestedEvents=2, GeneratedPrimaries=generated,
                        ProcessedEvents=processed, AbortedEvents=aborted).items()}
        for name, value in numbers.items():
            tree.Branch(name, value, name+'/I')
        tree.Fill(); tree.Write()
    file.Close()


# Zero hit rows are a successful generation fixture; nonempty Hits do not prove
# completion. Incomplete generation, processed-event and abort counters all fail.
for index, bad in enumerate([dict(accounting=False, hit=True), dict(generated=1),
                             dict(processed=1), dict(aborted=1)]):
    path = out/f'incomplete-{index}.root'; raw_fixture(path, **bad)
    rejects(lambda: inspect_raw(path, identity, 2))
path = out/'zero-hits.root'; raw_fixture(path)
assert inspect_raw(path, identity, 2)['GeneratedPrimaries'] == 2
assert inspect_raw(path, identity, 2)['hit_rows'] == 0

# Effective environment comes from a real fresh initialized simulation, no events.
probe = out/'probe'; probe.mkdir()
(probe/'probe.mac').write_text('/control/echo phase4-validation-no-transport\n')
env_log = runner.invoke([build/'rdecay01', probe/'probe.mac', '1', '--layout', config['layout']], probe, 'probe', 60)
environment = runner.parse_environment(env_log)
assert environment['source_hash'] == runner.compiled_source_hash()
assert float(environment['radioactive_decay_time_threshold_s']) > 0
assert set(environment) >= set(runner.ENV_KEYS)
rejects(lambda: runner.parse_environment(env_log.replace('CYGNO_ENV G4RADIOACTIVEDATA', 'missing G4RADIOACTIVEDATA')))
# Content changes must invalidate data identity, even if paths remain the same.
data = out/'synthetic-data-v1'; data.mkdir(); (data/'entry').write_text('one')
small_env = dict.fromkeys(runner.ENV_KEYS, str(data))
first_data = runner.dataset_state(small_env)
(data/'entry').write_text('two')
assert first_data != runner.dataset_state(small_env)

selected = ['GEMsCore_U238', 'GEMsCore_Th232', 'GEMsCore_K40']
args = argparse.Namespace(config=repo/'config/study/smoke-A.json', matrix=repo/'config/study/thesis-table7.1.json',
                          output=out/'campaign', build=build, only=selected, retry_failed=False)
real_invoke = runner.invoke
attempted = []
failing = {'GEMsCore_Th232'}


def synthetic_invoke(command, cwd, label, timeout):
    if label == 'environment':
        (cwd/'environment.log').write_text(env_log)
        return env_log
    if label == 'simulation':
        contribution = cwd.parent.name
        attempted.append(contribution)
        raw_fixture(cwd/'outfiles_V2/raw_t0.root', hit=contribution == 'GEMsCore_K40')
        runner.save(cwd/'simulation.command.json', dict(command=list(map(str, command)),
                    fixture=True, returncode=-6 if contribution in failing else 0))
        (cwd/'simulation.log').write_text(env_log+'\nSYNTHETIC RUNNER FIXTURE; NOT RADIOACTIVE TRANSPORT\n')
        if contribution in failing:
            raise RuntimeError('Injected failure AFTER writing a superficially valid ROOT file')
        return env_log
    return real_invoke(command, cwd, label, timeout)


with patch.object(runner, 'invoke', side_effect=synthetic_invoke), \
     patch.object(runner, 'dataset_state', return_value={'fixture': 'not a real physics campaign'}):
    assert runner.run(args) == 2
    assert attempted == selected
    jobs_dir = args.output/'jobs'
    first = runner.read(jobs_dir/selected[0]/'manifest.json')
    assert first['status'] == 'complete' and first['accounting']['hit_rows'] == 0
    failed = runner.read(jobs_dir/selected[1]/'manifest.json')
    assert failed['status'] == 'failed' and 'accounting' not in failed
    assert runner.read(args.output/'latest-report.json')['coverage'] == '2/26'
    before = runner.artifacts(jobs_dir/selected[0]/first['attempt'])
    assert runner.run(args) == 2  # complete jobs reused, failure retained
    assert attempted == selected
    failing.clear(); args.retry_failed = True
    assert runner.run(args) == 0
    assert attempted == selected+[selected[1]]
    assert runner.artifacts(jobs_dir/selected[0]/first['attempt']) == before
    assert (jobs_dir/selected[1]/'attempt-0001/manifest.json').is_file()
    assert runner.read(jobs_dir/selected[1]/'manifest.json')['attempt'] == 'attempt-0002'
    assert runner.read(args.output/'latest-report.json')['scientific_validity'] == 'unvalidated'
    # Resuming corrupted completed work is rejected even with --retry-failed.
    raw = jobs_dir/selected[0]/first['attempt']/'outfiles_V2/raw_t0.root'
    original = raw.read_bytes(); raw.write_bytes(original+b'corrupt')
    assert runner.run(args) == 2
    assert len(attempted) == 4
    raw.write_bytes(original)
    # Configuration, activity matrix and source/build identity are immutable.
    changed = out/'changed.json'
    changed.write_text(json.dumps(config | {'seed': config['seed']+1}))
    rejects(lambda: runner.run(argparse.Namespace(**(vars(args) | {'config': changed}))))
    modified = copy.deepcopy(matrix); modified['contributions'][0]['activity'] *= 2
    changed_matrix = out/'changed-matrix.json'; changed_matrix.write_text(json.dumps(modified))
    rejects(lambda: runner.run(argparse.Namespace(**(vars(args) | {'matrix': changed_matrix}))))
    with patch.object(runner, 'compiled_source_hash', return_value='stale'):
        rejects(lambda: runner.run(args))
    assert len(attempted) == 4
    # The default schedules ALL 26 contributions; these are synthetic outputs,
    # not a matrix Monte Carlo campaign or a claim of chain completeness.
    full_args = argparse.Namespace(**(vars(args) | {'output': out/'all-26', 'only': None}))
    assert runner.run(full_args) == 0
    full_report = runner.read(full_args.output/'latest-report.json')
    assert full_report['complete_matrix'] is True and full_report['coverage'] == '26/26'
    assert full_report['scientific_validity'] == 'unvalidated'
    report_dir = Path(full_report['path'])
    exported = runner.read(report_dir/'spectra.json')
    assert len(exported['windows']) == 312 and len(exported['categories']) == 84
    assert len(exported['density']) == 14
    assert 'Resistors U238 750 piece' in (report_dir/'normalization.tsv').read_text()

# Actual process nonzero/timeout receipts and a lock collision.
commands = out/'commands'; commands.mkdir()
rejects(lambda: real_invoke([sys.executable, '-c', 'raise SystemExit(7)'], commands, 'nonzero', 5))
assert runner.read(commands/'nonzero.command.json')['returncode'] == 7
rejects(lambda: real_invoke([sys.executable, '-c', 'import time; time.sleep(1)'], commands, 'timeout', .02))
assert runner.read(commands/'timeout.command.json')['timed_out'] is True
with runner.locked(out/'lock-test'):
    rejects(lambda: runner.run(argparse.Namespace(**(vars(args) | {'output': out/'lock-test'}))))
bad_config = out/'production.json'; bad_config.write_text(json.dumps(config | {'mode': 'production'}))
rejects(lambda: runner.load_config(bad_config))
assert runner.seeds_for(12345, selected[0]) == runner.seeds_for(12345, selected[0])
assert runner.macro_for(matrix['contributions'][0], config) == runner.macro_for(matrix['contributions'][0], config | {'layout': 'cygno-5x5x3-v1'})

# Exact thresholds intentionally straddle histogram bins. Both layouts use module
# zero, independent known coordinates, and boundary-inclusive 20 mm fiducial cuts.
energies = [-1., 0., 9.9, 10., 10.1, 400., 400.1, 1999.9, 2000., 2001.]
for layout, center in [('legacy-25x3', (-6048., -804., 250.25)),
                       ('cygno-5x5x3-v1', (-1008., -1608., -2035.05))]:
    directory = out/layout; directory.mkdir()
    source = directory/'processed.root'; file = ROOT.TFile(str(source), 'RECREATE')
    tree = ROOT.TTree('elabHits', 'synthetic boundary groups')
    event = array.array('i', [0]); tree.Branch('evNumber', event, 'evNumber/I')
    strings = {'PartName': ROOT.std.string('e-'), 'Nucleus': ROOT.std.string('fixture')}
    for name, value in strings.items(): tree.Branch(name, value)
    vectors = {name: ROOT.std.vector('double')() for name in ('EDep_Out', 'VolNnum_Out', 'X_Vertex', 'Y_Vertex', 'Z_Vertex')}
    for name, value in vectors.items(): tree.Branch(name, value)
    for i, energy in enumerate(energies+[10.1]):
        event[0] = i
        for name, value in dict(EDep_Out=energy/1000., VolNnum_Out=0.,
                                X_Vertex=center[0]+(230.001 if i == len(energies) else 230.),
                                Y_Vertex=center[1], Z_Vertex=center[2]).items():
            vectors[name].clear(); vectors[name].push_back(value)
        tree.Fill()
    tree.Write()
    for name, value in dict(CygnoLayout=layout, CygnoGeometry=identity['geometry_hash'],
                            CygnoDetectorModel='code-compatible', CygnoSourcePolicy='historical').items():
        ROOT.TNamed(name, value).Write()
    file.Close()
    norm = directory/'normalization.tsv'
    norm.write_text(f'# normalization-format: quantity-v2\n# layout: {layout}\n# detector-model: code-compatible\n# source-policy: historical\n# provenance: synthetic boundary test\n'+
                    f'GEMsCore K40 2 kg 1 Bq/kg 31536000 "GEMs" "{source}"\n')
    real_invoke([build/'analysis/PlotNormalizedSpectra', norm], directory, 'plot', 60)
    summary = export_spectra(directory/'NormalizedHisto.root', [{'id': 'GEMsCore_K40', 'category': 'GEMs'}])
    expected = {'all': 10, 'gt10': 6, 'gt10_le400': 2, 'underflow': 1, 'in_range': 7, 'overflow': 2}
    for window in summary['windows']:
        count = expected[window['window']] + (int(window['window'] in ('all', 'gt10', 'gt10_le400', 'in_range')) if not window['fiducial'] else 0)
        assert window['count'] == count, window
        assert window['rate_per_year'] == count*2 and window['variance_per_year2'] == count*4
    for density in summary['density']:
        integral = sum((b['high_keV']-b['low_keV'])*b['counts_per_keV_year'] for b in density['bins'])
        assert math.isclose(integral, 2*(7 if density['fiducial'] else 8))
        assert density['underflow_per_year'] == 2 and density['overflow_per_year'] == 4
print('PASS: runner completion/failure/resume/corruption/provenance guards, exact windows/flows and density for both layouts;', out)
