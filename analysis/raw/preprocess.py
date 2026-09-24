"""Literal historical state machine, including inherited ionizationSeen behavior.

Track identity does not drive grouping. Optional track_sink receives one diagnostic
record per event-local track at event end, using its first sensitive step labels.
"""
from analysis.common.model import Group, TrackRecord


def groups(chunks, track_sink=None):
    group = None
    event_id = None
    index = 0
    tracks = {}
    fields = ('EventNumber', 'ParticleName', 'Nucleus', 'ProcessType', 'VolumeNumber',
              'EnergyDeposit', 'x_hits', 'y_hits', 'z_hits', 'ParticleID', 'ParticleTag', 'ParentID')
    def flush_tracks():
        if track_sink is not None:
            for key in sorted(tracks):
                track_sink(tracks[key])
        tracks.clear()
    for chunk in chunks:
        for i, row in enumerate(zip(*(chunk[f] for f in fields))):
            event, particle, nucleus, process, volume, energy, x, y, z, track, tag, parent = row
            if event != event_id:
                if group is not None:
                    yield group
                group = None
                flush_tracks()
                event_id, index = int(event), 0
            if track_sink is not None and int(track) not in tracks:
                tracks[int(track)] = TrackRecord(int(event), int(track), int(tag), int(parent),
                                                 str(particle), str(nucleus), str(process))
            if particle not in ('e-', 'e+', 'alpha'):
                continue
            ionization = process in ('ionIoni', 'eIoni')
            if group is not None:
                if process == group.process and nucleus == group.nucleus and not group.ionization_seen:
                    group.particle = str(particle)
                elif ionization:
                    group.ionization_seen = True
                else:
                    yield group
                    group = None
            if group is None:
                group = Group(int(event), str(particle), str(nucleus), str(process), group_index=index)
                index += 1
            if track_sink is not None and int(track) not in group.track_ids:
                tracks[int(track)].group_indices.append(group.group_index)
            time = float(chunk['GlobalTime_ns'][i]) if 'GlobalTime_ns' in chunk else None
            group.add(int(volume), float(energy), float(x), float(y), float(z), time, int(track))
    if group is not None:
        yield group
    flush_tracks()
