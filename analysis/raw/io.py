"""Chunked uproot validation of explicit legacy/timed raw schemas (no CERN ROOT)."""
import numpy as np
import uproot
from study.runtime import ACCOUNTING_FIELDS, validate_accounting
from study.source_matrix import require, LAYOUT_MODULE_COUNTS

HITS_SCHEMA = dict(EventNumber='int32', ParticleName='string', ParticleID='int32',
                   ParticleTag='int32', ParentID='int32', x_hits='float64', y_hits='float64',
                   z_hits='float64', EnergyDeposit='float64', VolumeNumber='int32',
                   Nucleus='string', ProcessType='string')
from analysis.common.io import tree, scientific_header, output_metadata, METADATA
LEGACY_HITS_SCHEMA = HITS_SCHEMA.copy()
HITS_SCHEMA = HITS_SCHEMA | {'GlobalTime_ns':'float64'}


def header(file, expected, requested):
    accounting = scientific_header(file, expected, requested)
    metadata = output_metadata(file)
    require(metadata['OutputFormat'] in ('raw','both'), 'Raw representation unavailable')
    hits = tree(file, 'Hits', HITS_SCHEMA if metadata['OutputSchemaVersion'] else LEGACY_HITS_SCHEMA)
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
        for field in ('x_hits', 'y_hits', 'z_hits', 'EnergyDeposit', *(['GlobalTime_ns'] if 'GlobalTime_ns' in chunk else [])):
            require(np.all(np.isfinite(chunk[field])), 'Nonfinite Hits '+field)
        require(np.all(chunk['ParticleID'] > 0) and np.all(chunk['ParentID'] >= 0) and
                np.all(chunk['ParticleID'] != chunk['ParentID']), 'Invalid track identity')
        volumes = chunk['VolumeNumber']
        require(np.all((volumes >= 0) & (volumes < 2*LAYOUT_MODULE_COUNTS[layout])), 'Invalid gas copy')
        yield chunk


def inspect_raw(path, expected, requested, step_size='64 MB'):
    with uproot.open(path, array_cache=None) as file:
        accounting, hits = header(file, expected, requested)
        for _ in hit_chunks(hits, requested, expected['layout'], step_size):
            pass
        return accounting | {'hit_rows': int(hits.num_entries)}
