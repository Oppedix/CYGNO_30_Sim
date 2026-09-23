"""Literal streaming port of analysis/ProcessEvents.cc's historical grouping.

Nucleus is the most recently tracked ion, not per-hit ancestry. Group labels,
ionizationSeen initialization and first position in each volume are intentional.
"""
from dataclasses import dataclass, field


@dataclass
class Group:
    event: int
    particle: str
    nucleus: str
    process: str
    ionization_seen: bool = False
    volumes: dict = field(default_factory=dict)  # insertion order = C++ vectors

    def add(self, volume, energy, x, y, z):
        if volume in self.volumes:
            self.volumes[volume][0] += energy
        else:
            self.volumes[volume] = [energy, x, y, z]


def groups(chunks):
    group = None
    fields = ('EventNumber', 'ParticleName', 'Nucleus', 'ProcessType', 'VolumeNumber',
              'EnergyDeposit', 'x_hits', 'y_hits', 'z_hits')
    for chunk in chunks:
        for event, particle, nucleus, process, volume, energy, x, y, z in zip(*(chunk[f] for f in fields)):
            if group is not None and event != group.event:
                yield group
                group = None
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
                group = Group(int(event), str(particle), str(nucleus), str(process))
            group.add(int(volume), float(energy), float(x), float(y), float(z))
    if group is not None:
        yield group
