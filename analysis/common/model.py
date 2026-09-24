"""The only analysis group model. Times/provenance never select canonical spectra."""
from dataclasses import dataclass, field

@dataclass
class GroupVolume:
    energy: float
    x: float
    y: float
    z: float
    first_hit_time_ns: float | None = None

@dataclass
class Group:
    event: int
    particle: str
    nucleus: str
    process: str
    group_index: int = 0
    volumes: dict[int, GroupVolume] = field(default_factory=dict)
    step_count: int = 0
    track_ids: set[int] = field(default_factory=set)
    # Internal raw state, deliberately absent from storage/semantic equality.
    ionization_seen: bool = field(default=False, compare=False, repr=False)

    def add(self, volume, energy, x, y, z, time=None, track=None):
        self.step_count += 1
        if track is not None:
            self.track_ids.add(track)
        if volume in self.volumes:
            self.volumes[volume].energy += energy
        else:
            self.volumes[volume] = GroupVolume(energy, x, y, z, time)

@dataclass
class TrackRecord:
    event: int
    particle_id: int
    particle_tag: int
    parent_id: int
    particle: str
    nucleus: str
    process: str
    group_indices: list[int] = field(default_factory=list)
