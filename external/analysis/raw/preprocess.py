"""All-particle track × gas-volume accumulation; one event of state."""
from analysis.common.model import Group


def groups(chunks):
    event=None
    tracks={}
    for chunk in chunks:
        for i in range(len(chunk['EventNumber'])):
            row={key:values[i] for key,values in chunk.items()}
            if event!=row['EventNumber']:
                yield from tracks.values()
                tracks={};event=int(row['EventNumber'])
            key=int(row['ParticleID'])
            if key not in tracks:
                tracks[key]=Group(event,str(row['ParticleName']),str(row['Nucleus']),str(row['ProcessType']),group_index=len(tracks))
            tracks[key].add(int(row['VolumeNumber']),float(row['EnergyDeposit']),float(row['x_hits']),
                           float(row['y_hits']),float(row['z_hits']),float(row['GlobalTime_ns']),key)
    yield from tracks.values()
