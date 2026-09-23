"""Chunked uproot validation of unchanged Geant4 TTrees (no CERN ROOT)."""
import numpy as np
import uproot
from study.runtime import ACCOUNTING_FIELDS, validate_accounting
from study.source_matrix import require, LAYOUT_MODULE_COUNTS

HITS_SCHEMA = dict(EventNumber='int32', ParticleName='string', ParticleID='int32',
                   ParticleTag='int32', ParentID='int32', x_hits='float64', y_hits='float64',
                   z_hits='float64', EnergyDeposit='float64', VolumeNumber='int32',
                   Nucleus='string', ProcessType='string')
METADATA = dict(GeometryHash='geometry_hash', Layout='layout', DetectorModel='model', SourcePolicy='source_policy')
TYPES = {'int32': {'int32_t', 'int'}, 'float64': {'double'}, 'string': {'char*'}}


def tree(file, name, schema, one=False):
    require(name in file and file[name].classname == 'TTree', 'Missing/non-TTree '+name)
    result = file[name]
    require(set(result.keys()) == set(schema), 'Invalid '+name+' field names')
    for key, kind in schema.items():
        require(result[key].typename in TYPES[kind], f'Invalid {name}.{key} type: {result[key].typename}')
    if one:
        require(result.num_entries == 1, 'Need exactly one '+name+' row')
    return result


def header(file, expected, requested):
    metadata = tree(file, 'RunMetadata', dict.fromkeys(METADATA, 'string'), one=True).arrays(library='np')
    for field, key in METADATA.items():
        require(metadata[field][0] == expected[key], 'Raw identity mismatch: '+field)
    accounting_tree = tree(file, 'RunAccounting', dict.fromkeys(ACCOUNTING_FIELDS, 'int32'), one=True)
    accounting = {name: int(values[0]) for name, values in accounting_tree.arrays(library='np').items()}
    validate_accounting(accounting, requested)
    hits = tree(file, 'Hits', HITS_SCHEMA)
    return accounting, hits


def hit_chunks(hits, requested, layout, step_size='64 MB'):
    last_event = -1
    for chunk in hits.iterate(step_size=step_size, library='np'):
        events = chunk['EventNumber']
        if not len(events):
            continue
        require(np.all((events >= 0) & (events < requested)), 'Invalid event ID')
        require(events[0] >= last_event and np.all(events[1:] >= events[:-1]), 'Out-of-order single-worker events')
        last_event = int(events[-1])
        for field in ('x_hits', 'y_hits', 'z_hits', 'EnergyDeposit'):
            require(np.all(np.isfinite(chunk[field])), 'Nonfinite Hits '+field)
        volumes = chunk['VolumeNumber']
        require(np.all((volumes >= 0) & (volumes < 2*LAYOUT_MODULE_COUNTS[layout])), 'Invalid gas copy')
        yield chunk


def inspect_raw(path, expected, requested, step_size='64 MB'):
    with uproot.open(path, array_cache=None) as file:
        accounting, hits = header(file, expected, requested)
        for _ in hit_chunks(hits, requested, expected['layout'], step_size):
            pass
        return accounting | {'hit_rows': int(hits.num_entries)}
