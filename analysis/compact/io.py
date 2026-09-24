"""Strict typed trees; all relationships are checked by preprocess.groups."""
from analysis.common.io import tree, output_metadata, scientific_header
from study.source_matrix import require
GROUPS_SCHEMA = dict(EventNumber='int32', GroupIndex='int32', ParticleName='string', Nucleus='string',
                     ProcessType='string', StepCount='int32', TrackCount='int32', VolumeCount='int32')
VOLUMES_SCHEMA = dict(EventNumber='int32', GroupIndex='int32', VolumeOrder='int32', VolumeNumber='int32',
    EnergyDeposit='float64', x_first='float64', y_first='float64', z_first='float64', FirstHitTime_ns='float64')
TRACKS_SCHEMA = dict(EventNumber='int32', ParticleID='int32', ParticleTag='int32', ParentID='int32',
                    ParticleName='string', Nucleus='string', ProcessType='string', GroupIndex='int32')
LINKS_SCHEMA = dict(EventNumber='int32', ParticleID='int32', GroupIndex='int32')
SCHEMAS = dict(Groups=GROUPS_SCHEMA, GroupVolumes=VOLUMES_SCHEMA, Tracks=TRACKS_SCHEMA, TrackGroups=LINKS_SCHEMA)


def header(file, expected, requested):
    accounting = scientific_header(file, expected, requested)
    require(output_metadata(file)['OutputFormat'] in ('compact','both'), 'Compact representation unavailable')
    return accounting, {name: tree(file,name,schema) for name,schema in SCHEMAS.items()}
