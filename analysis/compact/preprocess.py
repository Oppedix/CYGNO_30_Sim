"""Reconstruct canonical objects; never regroup compact data.

Merge sorted tree streams by event; validate keys, ordering, counts, foreign keys,
and track membership before exposing that event. Memory is bounded by one event
plus four uproot chunks. Tracks use first sensitive-step provenance.
"""
from itertools import groupby
import math
from analysis.common.io import rows
from analysis.common.model import Group, GroupVolume, TrackRecord
from study.source_matrix import require, LAYOUT_MODULE_COUNTS


def event_rows(tree, requested, step_size):
    last = -1
    for event, batch in groupby(rows(tree, step_size), lambda row: row['EventNumber']):
        require(last < event < requested and event >= 0, 'Invalid/out-of-order compact event')
        last = event
        yield event, list(batch)


def reconstruct(event, data, layout):
    groups = {}
    for row in data['Groups']:
        key = row['GroupIndex']
        require(key == len(groups), 'Duplicate/out-of-order GroupIndex')
        require(row['ParticleName'] in ('e-','e+','alpha'), 'Invalid group particle')
        require(row['StepCount'] >= row['TrackCount'] > 0 and
                row['StepCount'] >= row['VolumeCount'] > 0, 'Invalid group counts')
        groups[key] = Group(event, row['ParticleName'], row['Nucleus'], row['ProcessType'],
                            group_index=key, step_count=row['StepCount'])
    previous = (-1,-1)
    for row in data['GroupVolumes']:
        key = row['GroupIndex']
        require(key in groups, 'Orphan group volume')
        group = groups[key]
        volume = row['VolumeNumber']
        order = row['VolumeOrder']
        require((key,order) > previous and order==len(group.volumes), 'Invalid VolumeOrder')
        require(volume not in group.volumes, 'Duplicate group/volume key')
        require(0 <= volume < 2*LAYOUT_MODULE_COUNTS[layout], 'Invalid compact gas copy')
        values = [row[k] for k in ('EnergyDeposit','x_first','y_first','z_first','FirstHitTime_ns')]
        require(all(math.isfinite(v) for v in values), 'Nonfinite group volume')
        group.volumes[volume] = GroupVolume(*values)
        previous = (key,order)
    tracks = {}
    sentinels = {}
    last_track = 0
    for row in data['Tracks']:
        key = row['ParticleID']
        require(key > last_track and row['ParentID'] >= 0 and row['ParentID'] != key,
                'Duplicate/invalid/out-of-order track identity')
        expected_tag = {'e-':0,'e+':1,'gamma':2,'alpha':3}.get(row['ParticleName'],-1)
        require(row['ParticleTag']==expected_tag, 'Invalid ParticleTag')
        tracks[key] = TrackRecord(event,key,row['ParticleTag'],row['ParentID'],row['ParticleName'],
                                   row['Nucleus'],row['ProcessType'])
        sentinels[key] = row['GroupIndex']
        last_track = key
    previous = (-1,-1)
    for row in data['TrackGroups']:
        track, key = row['ParticleID'], row['GroupIndex']
        require(track in tracks and key in groups, 'Orphan track/group relationship')
        require((track,key)>previous, 'Duplicate/out-of-order track/group relationship')
        require(tracks[track].particle in ('e-','e+','alpha'), 'Ignored particle has group')
        tracks[track].group_indices.append(key)
        groups[key].track_ids.add(track)
        previous=(track,key)
    for key, track in tracks.items():
        links = track.group_indices
        require(bool(links)==(track.particle in ('e-','e+','alpha')), 'Missing/unexpected track membership')
        require(sentinels[key]==(-1 if not links else links[0] if len(links)==1 else -2),
                'Track GroupIndex sentinel/relationship mismatch')
    for row in data['Groups']:
        group=groups[row['GroupIndex']]
        require(len(group.volumes)==row['VolumeCount'] and len(group.track_ids)==row['TrackCount'],
                'Group relationship count mismatch')
    return list(groups.values()), list(tracks.values())


def groups(trees, requested, layout, step_size='64 MB', track_sink=None):
    streams = {name: iter(event_rows(tree, requested, step_size)) for name,tree in trees.items()}
    pending = {name: next(stream,None) for name,stream in streams.items()}
    while any(value is not None for value in pending.values()):
        event = min(value[0] for value in pending.values() if value is not None)
        data = {name: value[1] if value is not None and value[0]==event else []
                for name,value in pending.items()}
        canonical, tracks = reconstruct(event,data,layout)
        yield from canonical
        if track_sink is not None:
            for track in tracks:
                track_sink(track)
        for name,value in pending.items():
            if value is not None and value[0]==event:
                pending[name]=next(streams[name],None)
