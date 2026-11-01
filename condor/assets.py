#!/usr/bin/env python3
"""One-time frozen Linux runtime preparation and worker preflight (stdlib only)."""
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from study import runtime as rt
from study.source_matrix import require
from external.study.simulate import environment, check_model
from external.study.config import load


def probe(build, directory, cfg):
    directory.mkdir(parents=True)
    macro = directory/'probe.mac'; macro.write_text('/control/echo FROZEN_ENVIRONMENT_PROBE\n')
    log = rt.invoke([build/'rdecay01', macro, '1', '--mode', 'external', '--shield', 'copper20',
                     '--layout', 'cygno-11x7-v1', '--output-mode', 'compact', '--model', cfg['model']],
                    directory, 'environment', 120)
    check_model(log, cfg)
    env, radius, geometry = environment(log)
    require(re.search(r'\b(?:11\.3\.1|geant4-11-03-patch-01)\b', env['geant4']), 'Requires actual Geant4 11.3.1; no fallback')
    require('[MT]' not in env['geant4'], 'Require the custom serial Geant4 11.3.1 binary')
    require(env['source_hash'] == rt.compiled_source_hash() and
            env['geometry_hash'] == rt.digest(rt.REPO/'common/DetectorGeometry.hh') and
            geometry == rt.digest(rt.REPO/'common/ExternalGeometry.hh'), 'Stale executable: rebuild this source')
    return dict(environment=env, source_radius_mm=radius, external_geometry_hash=geometry,
                datasets=rt.dataset_state(env))


def comparable(record):
    return record | dict(environment={k: v for k, v in record['environment'].items() if k not in rt.ENV_KEYS},
                         datasets={k: {n: v for n, v in d.items() if n == 'content_sha256' or n == 'files'}
                                   for k, d in record['datasets'].items()})


def filemap(root):
    return {str(p.relative_to(root)): rt.digest(p) for p in sorted(root.rglob('*')) if p.is_file() and p.name != 'inventory.json'}


def freeze_source(destination, state):
    for name, checksum in state['files_sha256'].items():
        # source_state marks tracked directory aliases as 'missing'; they are not external runtime inputs.
        if checksum == 'missing': continue
        source = rt.REPO/name
        require(source.resolve().is_relative_to(rt.REPO), 'Source link escapes checkout')
        target = destination/name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        require(rt.digest(target) == checksum, 'Source changed while freezing')


def prepare(build, destination, timeout):
    require(platform.system() == 'Linux' and sys.version_info >= (3, 10), 'Prepare on Linux with Python >=3.10, not the laptop')
    require(1 <= timeout <= 2147483647, 'Invalid runner timeout')
    build, destination = build.resolve(), destination.resolve()
    require(not destination.exists() and not destination.is_relative_to(rt.REPO), 'Use a NEW assets directory outside the repository')
    state = rt.source_state()
    require(not state['status'], 'Commit all source changes before freezing assets')
    cache = (build/'CMakeCache.txt').read_text()
    match = re.search(r'^Geant4_DIR:[^=]+=(.+)$', cache, re.M)
    require(match, 'Missing Geant4 CMake provenance')
    g4config = (Path(match[1])/'Geant4Config.cmake').read_text()
    require(re.search(r'set\(Geant4_multithreaded_FOUND\s+OFF\)', g4config), 'Require the custom serial Geant4 build')
    for name in ('rdecay01', 'geometry_quantities'):
        with (build/name).open('rb') as binary:
            require(binary.read(4) == b'\x7fELF', 'Requires Linux ELF binaries')
    os.environ.update(G4FORCENUMBEROFTHREADS='1', G4RUN_MANAGER_TYPE='Serial', OMP_NUM_THREADS='1')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='cygno-assets-', dir=destination.parent) as tmp:
        top = Path(tmp); root = top/'runtime'; root.mkdir()
        for d in ('source', 'build', 'lib', 'datasets'): (root/d).mkdir()
        freeze_source(root/'source', state)
        libraries = {}
        for name in ('rdecay01', 'geometry_quantities'):
            shutil.copy2(build/name, root/'build'/name)
            log = subprocess.check_output(['ldd', str(build/name)], text=True)
            (top/(name+'.ldd')).write_text(log)
            require('not found' not in log, 'Unresolved build library dependency')
            for soname, path in re.findall(r'^\s*(\S+) => (/\S+) ', log, re.M):
                # libc and the image's system ABI must work; never bundle a private loader/libc.
                if path.startswith(('/lib/', '/lib64/', '/usr/lib/', '/usr/lib64/')): continue
                target = root/'lib'/soname
                checksum = rt.digest(Path(path))
                require(soname not in libraries or libraries[soname] == checksum, 'Conflicting library SONAME')
                libraries[soname] = checksum; shutil.copyfile(path, target)
        compiler_info = list((build/'CMakeFiles').glob('*/CMakeCXXCompiler.cmake'))
        require(len(compiler_info) == 1, 'Missing/unambiguous compiler provenance required')
        worker_build = dict(machine=platform.machine(), geant4_config_sha256=rt.digest(Path(match[1])/'Geant4Config.cmake'),
                            libraries=libraries, compiler=compiler_info[0].read_text(),
                            flags=[line for line in cache.splitlines() if re.match(r'^(CMAKE_(CXX_FLAGS[^:]*|BUILD_TYPE|EXE_LINKER_FLAGS[^:]*)):', line)])
        rt.save(root/'source'/'.frozen-source.json', state | dict(worker_build=worker_build))
        configs = {}
        for particle, name in [('gamma', 'hall-c-gamma-2026-proxy.json'), ('neutron', 'hall-c-neutron-wulandari-proxy.json')]:
            cfg = load(rt.REPO/'external/config'/name); cfg['timeout_seconds'] = timeout
            rt.save(root/(particle+'.json'), cfg); configs[particle] = cfg
        record = probe(build, top/'prepare-probe', configs['gamma'])
        rt.invoke([build/'geometry_quantities', top/'prepare-probe'/'quantities.tsv', 'cygno-11x7-v1',
                   top/'prepare-probe'/'geometry.json', '--mode', 'external', '--model', configs['gamma']['model']],
                  top/'prepare-probe', 'geometry', 120)
        geometry = rt.read(top/'prepare-probe'/'geometry.json')
        require(geometry['source_hash'] == record['environment']['source_hash'] and
                geometry['geometry_hash'] == record['environment']['geometry_hash'] and
                geometry['model'] == configs['gamma']['model'] and geometry['layout'] == 'cygno-11x7-v1',
                'Stale/incompatible geometry exporter')
        for key, data in record['datasets'].items():
            print('Freezing dataset '+key, flush=True)
            shutil.copytree(data['path'], root/'datasets'/key, symlinks=False)
        record['machine'] = platform.machine()
        rt.save(root/'requirements.json', record)
        rt.save(root/'inventory.json', filemap(root))
        archive = top/'worker-assets.tar'
        with tarfile.open(archive, 'w') as tar:
            for path in sorted(root.rglob('*')):
                if path.is_file(): tar.add(path, arcname=str(path.relative_to(root)), recursive=False)
        # Keep preparation receipts outside source: the worker receives only its frozen assets.
        sha = rt.digest(archive)
        (top/'worker-assets.tar.sha256').write_text(sha+'  worker-assets.tar\n')
        worker = top/'run_geant4_worker.sh'
        shutil.copy2(rt.REPO/'condor/run_geant4_worker.sh', worker)
        (top/'submission-assets.sha256').write_text(sha+'  worker-assets.tar\n'+rt.digest(worker)+'  run_geant4_worker.sh\n')
        require(rt.source_state() == state, 'Source changed during preparation')
        for name in ('rdecay01', 'geometry_quantities'):
            require(rt.digest(build/name) == rt.digest(root/'build'/name), 'Executable changed during preparation')
        destination.mkdir()
        for p in (archive, top/'worker-assets.tar.sha256', top/'prepare-probe', top/'rdecay01.ldd', top/'geometry_quantities.ldd', worker, top/'submission-assets.sha256'):
            shutil.move(str(p), destination/p.name)
        print('Prepared '+str(destination)+'; SHA256='+sha)
        print('This is preparation-host evidence only; the actual worker performs its own preflight.')


def check(root):
    require(platform.system() == 'Linux' and sys.version_info >= (3, 10), 'Worker requires Linux and Python >=3.10')
    require(rt.read(root/'inventory.json') == filemap(root), 'Frozen asset inventory/SHA256 mismatch')
    for name in ('rdecay01', 'geometry_quantities'):
        linked = subprocess.check_output(['ldd', str(root/'build'/name)], text=True)
        require('not found' not in linked, 'Missing worker dependency')
        resolved = dict(re.findall(r'^\s*(\S+) => (/\S+) ', linked, re.M))
        for library in (root/'lib').iterdir():
            if library.name in resolved:
                require(rt.digest(Path(resolved[library.name])) == rt.digest(library),
                        'Worker resolved a different library: '+library.name)
    record = probe(root/'build', root.parent/'worker-preflight', rt.read(root/'gamma.json'))
    record['machine'] = platform.machine()
    require(comparable(record) == comparable(rt.read(root/'requirements.json')), 'Worker physics/libraries/datasets differ from frozen requirements')
    print('Worker Geant4 11.3.1, binary/source, datasets and ABI preflight passed')


if __name__ == '__main__':
    try:
        if sys.argv[1] == 'prepare': prepare(Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4]))
        elif sys.argv[1] == 'check': check(Path(sys.argv[2]).resolve())
        else: raise ValueError('Expected prepare or check')
    except (ValueError, RuntimeError, OSError, KeyError, subprocess.SubprocessError) as e:
        print('Worker assets: '+str(e)+'; verify Linux/ELF ABI, serial Geant4 11.3.1 and datasets. No alternate Geant4 is used.', file=sys.stderr)
        sys.exit(1)
