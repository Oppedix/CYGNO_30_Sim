"""Format dispatch ends here. Every caller receives the same canonical Group."""
from analysis.common.io import output_metadata
from analysis.raw.io import header as raw_header, hit_chunks
from analysis.raw.preprocess import groups as raw_groups
from analysis.compact.io import header as compact_header
from analysis.compact.preprocess import groups as compact_groups
from analysis.compact.parity import validate


def canonical_input(file, expected, requested, geometry, step_size='64 MB', mode=None, version=None, reference_sink=None):
    metadata=output_metadata(file,mode,version)
    parity=None
    if metadata['OutputFormat']=='both':
        parity=validate(file,expected,requested,geometry,step_size,reference_sink)
    if metadata['OutputFormat']=='raw':
        accounting,hits=raw_header(file,expected,requested)
        stream=raw_groups(hit_chunks(hits,requested,expected['layout'],step_size))
    else:
        accounting,trees=compact_header(file,expected,requested)
        stream=compact_groups(trees,requested,expected['layout'],step_size)
    provenance=dict(output_format=metadata, parity=parity,
                    hit_rows=int(file['Hits'].num_entries) if 'Hits' in file else None)
    return accounting,stream,provenance
