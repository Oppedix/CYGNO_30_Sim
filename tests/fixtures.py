"""Small synthetic TTrees; fixtures are software tests, never Monte Carlo data."""
import json
from pathlib import Path
import numpy as np
import uproot
from study import runtime as rt
from study.raw_io import HITS_SCHEMA, METADATA
from study.source_matrix import COMPONENTS, read_matrix


def chunk(rows):
    defaults = dict(EventNumber=0, ParticleName='e-', ParticleID=1, ParticleTag=0, ParentID=0,
                    x_hits=0., y_hits=0., z_hits=0., EnergyDeposit=.001, VolumeNumber=0,
                    Nucleus='Pb208[2614.522000000000000]', ProcessType='RadioactiveDecay')
    records = [defaults | row for row in rows]
    return {key: np.array([row[key] for row in records], dtype=object if kind == 'string' else kind)
            for key, kind in HITS_SCHEMA.items()}


def raw_fixture(path, expected, rows=(), requested=2, accounting=None, schema=None, metadata=None, metadata_rows=1, accounting_rows=1):
    path.parent.mkdir(parents=True, exist_ok=True)
    with uproot.recreate(path) as file:
        file.mktree('Hits', schema or HITS_SCHEMA)
        if rows:
            values = chunk(rows)
            if schema:
                values = {k: v.astype(object if kind == 'string' else kind) for k, kind in schema.items() for v in [values[k]]}
            file['Hits'].extend(values)
        file.mktree('RunMetadata', dict.fromkeys(METADATA, 'string'))
        if metadata_rows:
            file['RunMetadata'].extend({k: [v]*metadata_rows for k,v in (metadata or {k:expected[v] for k,v in METADATA.items()}).items()})
        file.mktree('RunAccounting', dict.fromkeys(rt.ACCOUNTING_FIELDS, 'int32'))
        values = dict(RunID=0, RequestedEvents=requested, GeneratedPrimaries=requested, ProcessedEvents=requested, AbortedEvents=0)
        if accounting_rows:
            file['RunAccounting'].extend({k:np.array([v]*accounting_rows, dtype='int32') for k,v in (values | (accounting or {})).items()})


def environment():
    return dict.fromkeys(rt.ENV_KEYS, '/fixture/data') | dict(source_hash='fixture-source',
        geometry_hash=rt.digest(rt.REPO/'common/DetectorGeometry.hh'), geant4='fixture',
        physics='QGSP_BIC_EMZ+G4RadioactiveDecayPhysics', radioactive_decay_time_threshold_s=str(rt.RDM_SECONDS))


def log_for(env, requested):
    return '\n'.join('CYGNO_ENV '+k+' '+v for k,v in env.items())+'\n'+(
        f'CYGNO_RUN radioactive_decay_time_threshold_s {rt.RDM_SECONDS}\nCYGNO_ACCOUNTING '+json.dumps(dict(
        RunID=0, RequestedEvents=requested, GeneratedPrimaries=requested, ProcessedEvents=requested, AbortedEvents=0))+'\n')


def campaign_fixture(root):
    root.mkdir()
    cfg = rt.load_config(rt.REPO/'config/study/samuele.json') | dict(mode='smoke', primaries_per_job=2)
    matrix = read_matrix(rt.REPO/'config/study/thesis-table7.1.json')
    env = environment()
    identity = dict(config=cfg, matrix=matrix, effective_environment=env, source={'files_sha256': {}})
    rt.save(root/'config.json', cfg)
    rt.save(root/'matrix.json', matrix)
    # Arbitrary synthetic geometry: intentionally not a detector implementation.
    geometry = dict(layout=cfg['layout'], geometry_hash=env['geometry_hash'], source_hash=env['source_hash'],
                    gas_size_mm=[100,100,100], gas_centers_mm={str(i):[0,0,0] for i in range(150)})
    rt.save(root/'geometry.json', geometry)
    quantities = {name:dict(mass_kg=2., pieces=3, geometry_material='fixture') for name in COMPONENTS}
    (root/'quantities.tsv').write_text(f"# layout: {cfg['layout']}\n# detector-model: code-compatible\n# source-policy: historical\n# geometry-hash: {env['geometry_hash']}\n# compiled-source-hash: {env['source_hash']}\n# provenance: synthetic fixture\ncomponent\tmass_kg\tpieces\tgeometry_material\n"+''.join(f'{name}\t2\t3\tfixture\n' for name in COMPONENTS))
    checks = {name:dict(status='passed', PART122=False, environment=env) for name in
              ('u238-default', 'u238-enabled', 'th232-full', 'bi212-full')}
    preflight = root/'preflight'; preflight.mkdir()
    rt.save(preflight/'preflight.json', dict(complete=True, checks=checks))
    campaign = dict(schema_version=2, stage='simulation', identity=identity, fingerprint=rt.object_digest(identity),
                    quantities=quantities, limitations=['SYNTHETIC SOFTWARE TEST'], preflight='preflight/preflight.json',
                    preflight_artifacts=rt.artifacts(preflight), snapshots={name:rt.digest(root/name) for name in
                    ('config.json','matrix.json','geometry.json','quantities.tsv')})
    rt.save(root/'campaign.json', campaign)
    return cfg, matrix, campaign


def fake_invoke(command, cwd, label, timeout, **options):
    cfg = rt.read(cwd.parents[2]/'config.json')
    env = environment()
    expected = dict(layout=cfg['layout'],model=cfg['model'],source_policy=cfg['source_policy'],geometry_hash=env['geometry_hash'])
    raw_fixture(cwd/'outfiles_V2/raw.root', expected, [dict(EnergyDeposit=.02), dict(EventNumber=1,EnergyDeposit=.4)], cfg['primaries_per_job'])
    log = log_for(env, cfg['primaries_per_job'])
    (cwd/(label+'.log')).write_text(log)
    rt.save(cwd/(label+'.command.json'), dict(command=list(map(str,command)), returncode=0))
    return log
