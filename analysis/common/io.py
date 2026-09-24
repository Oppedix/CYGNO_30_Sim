"""Explicit storage contracts and scientific identity validation."""
from study.runtime import ACCOUNTING_FIELDS, validate_accounting
from study.source_matrix import require

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


def scientific_header(file, expected, requested):
    metadata = tree(file, 'RunMetadata', dict.fromkeys(METADATA, 'string'), one=True).arrays(library='np')
    for field, key in METADATA.items():
        require(metadata[field][0] == expected[key], 'Scientific identity mismatch: '+field)
    accounting_tree = tree(file, 'RunAccounting', dict.fromkeys(ACCOUNTING_FIELDS, 'int32'), one=True)
    accounting = {name: int(values[0]) for name, values in accounting_tree.arrays(library='np').items()}
    validate_accounting(accounting, requested)
    return accounting



OUTPUT_SCHEMA_VERSION = 1
PROCESSING_VERSION = 'event-boundaries-and-eof-v2'
TIMING_DEFINITION = 'pre-step global time / ns; Geant4 event-relative, not inter-event time'
FORMAT_SCHEMA = dict(OutputFormat='string', OutputSchemaVersion='int32', TimingDefinition='string',
                     CompactProcessingVersion='string')


def output_metadata(file, expected_mode=None, expected_version=None):
    if 'OutputMetadata' not in file:
        # Explicit legacy contract: old 12-column raw files only; schema checked by raw reader.
        require('Hits' in file and not any(k in file for k in ('Groups','GroupVolumes','Tracks','TrackGroups')),
                'Missing output metadata for compact format')
        result = dict(OutputFormat='raw', OutputSchemaVersion=0, TimingDefinition='unavailable',
                      CompactProcessingVersion=PROCESSING_VERSION)
    else:
        values = tree(file, 'OutputMetadata', FORMAT_SCHEMA, one=True).arrays(library='np')
        result = {key: int(v[0]) if key=='OutputSchemaVersion' else str(v[0]) for key,v in values.items()}
        require(result['OutputFormat'] in ('raw','compact','both'), 'Unknown output format')
        require(result['OutputSchemaVersion']==OUTPUT_SCHEMA_VERSION, 'Unsupported output schema version')
        require(result['TimingDefinition']==TIMING_DEFINITION and
                result['CompactProcessingVersion']==PROCESSING_VERSION, 'Unsupported timing/processing definition')
        mode=result['OutputFormat']
        require(('Hits' in file)==(mode!='compact'), 'Hits/output format disagreement')
        for key in ('Groups','GroupVolumes','Tracks','TrackGroups'):
            require((key in file)==(mode!='raw'), key+'/output format disagreement')
    if expected_mode is not None:
        require(result['OutputFormat']==expected_mode, 'Output mode/manifest mismatch')
    if expected_version is not None:
        require(result['OutputSchemaVersion']==expected_version, 'Output schema/manifest mismatch')
    return result


def rows(tree, step_size='64 MB'):
    for chunk in tree.iterate(step_size=step_size, library='np'):
        for i in range(len(next(iter(chunk.values())))):
            yield {key: value[i].item() if hasattr(value[i], 'item') else value[i] for key,value in chunk.items()}
