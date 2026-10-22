"""External identity guard; internal files cannot be normalized as environmental runs."""
from itertools import zip_longest
import math
from analysis.common.io import tree, scientific_header, output_metadata
from analysis.raw.io import HITS_SCHEMA, hit_chunks
from analysis.compact.io import SCHEMAS
from external.analysis.raw.preprocess import groups as raw_groups
from external.analysis.compact.preprocess import groups as compact_groups
from external.study.config import PROCESSING, PHYSICS
from study.source_matrix import require

SIMULATION_SCHEMA=dict.fromkeys(('Mode','Shielding','PhysicsList','SourceHash','ExternalGeometryHash'),'string')|{'SourceRadius_mm':'float64'}


def header(file,campaign):
    identity=campaign['identity'];cfg=identity['config']
    expected=dict(layout=cfg['layout'],model='cygno-300elj-v2',source_policy='environmental-surface-v1',geometry_hash=identity['environment']['geometry_hash'])
    scientific_header(file,expected,cfg['primaries'])
    fmt=output_metadata(file,cfg['output_mode'],1,processing=PROCESSING)
    values=tree(file,'SimulationMetadata',SIMULATION_SCHEMA,one=True).arrays(library='np')
    expected_sim=dict(Mode='external',Shielding=cfg['shield'],PhysicsList=PHYSICS,SourceHash=identity['environment']['source_hash'],ExternalGeometryHash=identity['external_geometry_hash'],SourceRadius_mm=identity['source_radius_mm'])
    require(all(values[k][0]==v for k,v in expected_sim.items()),'External transport metadata mismatch')
    require(math.isfinite(identity['source_radius_mm']) and identity['source_radius_mm']>0,'Invalid source surface')
    return fmt


def groups(file,campaign,step_size='64 MB'):
    fmt=header(file,campaign);cfg=campaign['identity']['config']
    if fmt['OutputFormat']!='compact':
        hits=tree(file,'Hits',HITS_SCHEMA)
        raw=raw_groups(hit_chunks(hits,cfg['primaries'],cfg['layout'],step_size))
    if fmt['OutputFormat']!='raw':
        trees={name:tree(file,name,schema) for name,schema in SCHEMAS.items()}
        compact=compact_groups(trees,cfg['primaries'],cfg['layout'],step_size)
    if fmt['OutputFormat']=='both':
        sentinel=object()
        for a,b in zip_longest(raw,compact,fillvalue=sentinel):
            require(a==b,'External raw/compact parity mismatch')
            yield b
    else:
        yield from raw if fmt['OutputFormat']=='raw' else compact
