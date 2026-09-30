"""Small semantic oracle for compact topology; historical spectra stay unchanged.

Consumes ordered canonical Groups, buffering only one event. Unlike spectra.py,
this opt-in study requires finite stored times; legacy raw None times are errors.
Group is inherited bookkeeping, not necessarily one interaction or one track.
"""
from itertools import groupby
import math
from analysis.common.spectra import fiducial

SELECTIONS = ('no_cut', 'fiducial_20mm', 'fiducial_20mm_single_volume',
              'fiducial_20mm_single_volume_prompt_single_site')


def active_volumes(group):
    """Positive TOTAL volume deposits only; a zero-energy touch is not a site."""
    return [volume for volume in group.volumes.values() if volume.energy > 0]


def selection_decisions(groups, geometry, coincidence_ns=1., multisite_distance_mm=10.):
    """Yield (Group, four nested flags), retaining input order, including non-ER.

    Candidate site = the sole active volume's stored first position/time, not
    necessarily the first positive step. Other ER groups supply all active sites,
    regardless of their own fiducial/single-volume status. No MC truth is used.
    Same-group/same-volume physical sites cannot be resolved in compact data.
    """
    if not math.isfinite(coincidence_ns) or coincidence_ns <= 0:
        raise ValueError('coincidence_ns must be positive and finite')
    if not math.isfinite(multisite_distance_mm) or multisite_distance_mm <= 0:
        raise ValueError('multisite_distance_mm must be positive and finite')
    previous_event = -1
    for event, batch in groupby(groups, lambda group: group.event):
        if event <= previous_event:
            raise ValueError('Groups must be ordered by increasing EventNumber')
        previous_event = event
        event_groups = list(batch)
        sites = []
        for group in event_groups:
            er = group.particle in ('e-', 'e+')
            if er:
                for volume in group.volumes.values():
                    values = (volume.energy, volume.x, volume.y, volume.z, volume.first_hit_time_ns)
                    if any(value is None or not math.isfinite(value) for value in values):
                        raise ValueError('Topology requires finite positions, energy and stored times')
            sites.append(active_volumes(group) if er else [])
        for i, group in enumerate(event_groups):
            er = group.particle in ('e-', 'e+')
            inside = er and fiducial(group, geometry)
            single_volume = inside and len(sites[i]) == 1
            single_site = single_volume
            if single_volume:
                candidate = sites[i][0]
                for j, partners in enumerate(sites):
                    if i == j:
                        continue
                    for partner in partners:
                        dt = abs(candidate.first_hit_time_ns - partner.first_hit_time_ns)
                        dx, dy, dz = candidate.x-partner.x, candidate.y-partner.y, candidate.z-partner.z
                        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                        if dt <= coincidence_ns and distance > multisite_distance_mm:
                            single_site = False
            yield group, (er, inside, single_volume, single_site)
