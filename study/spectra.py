"""Historical main plotter: 900 bins, first-position cut, exact unbinned windows."""
import math
import numpy as np
from study.source_matrix import quantity_for, require

WINDOWS = ('all', 'gt10', 'gt10_le400', 'underflow', 'in_range', 'overflow')
BOUNDARIES = dict(all='all finite energies, including underflow and overflow',
    gt10='E > 10 keV, no upper limit', gt10_le400='10 < E <= 400 keV',
    underflow='E < 0 keV', in_range='0 <= E < 2000 keV', overflow='E >= 2000 keV')
BINS = 900
MAX_ENERGY = 2000.


def window_flags(energy):
    require(math.isfinite(energy), 'Nonfinite group energy')
    return (True, energy > 10, 10 < energy <= 400, energy < 0, 0 <= energy < 2000, energy >= 2000)


def fiducial(group, geometry):
    volume, (_, x, y, z) = next(iter(group.volumes.items()))
    center = geometry['gas_centers_mm'][str(volume)]
    return all(abs(pos-c) <= size/2-20 for pos, c, size in zip((x,y,z), center, geometry['gas_size_mm']))


def scale_for(row, quantities, generated):
    require(type(generated) is int and generated > 0, 'Invalid actual generated count')
    # Preserve C++ multiplication order, including the 365-day year.
    return row['activity']*quantity_for(row, quantities)*60*60*24*365/generated


def histogram_bin(energy):
    # ROOT 6.40 TAxis::FindBin, including rounding corrections at uniform edges.
    # https://root.cern.ch/doc/master/TAxis_8cxx_source.html
    if energy < 0:
        return 0
    if energy >= MAX_ENERGY:
        return BINS+1
    width = MAX_ENERGY/BINS
    approximate = int(energy/width)
    return 1+approximate-int(energy < width*approximate)+int(width*(approximate+1) <= energy)


def accumulate(groups, geometry):
    counts = np.zeros((2, 6), dtype=np.int64)
    histograms = np.zeros((2, BINS+2), dtype=np.int64)
    processed = 0
    for group in groups:
        processed += 1
        if group.particle not in ('e-', 'e+'):
            continue
        # C++ multiplies EACH volume energy by 1000 before summation.
        energy = 0.
        for values in group.volumes.values():
            energy += values[0]*1000
        flags = window_flags(energy)
        cut = fiducial(group, geometry)
        index = histogram_bin(energy)
        for c in range(2 if cut else 1):
            counts[c] += flags
            histograms[c, index] += 1
    return counts, histograms, processed


def summarize(contributions):
    """Each item: (matrix row, scale, counts, histogram); scale before summing."""
    windows, categories, totals, histograms = [], {}, {}, {}
    for row, scale, counts, histogram in contributions:
        for cut in (0, 1):
            for w, window in enumerate(WINDOWS):
                count = int(counts[cut, w])
                item = dict(contribution=row['id'], window=window, fiducial=cut, count=count,
                            rate_per_year=count*scale, variance_per_year2=count*scale*scale)
                windows.append(item)
                for target, label in ((categories, row['category']), (totals, 'total')):
                    aggregate = target.setdefault((label, window, cut), dict(category=label, window=window,
                        fiducial=cut, count=0, rate_per_year=0., variance_per_year2=0.))
                    for key in ('count', 'rate_per_year', 'variance_per_year2'):
                        aggregate[key] += item[key]
            h, variance = histograms.setdefault((row['category'], cut), (np.zeros(BINS+2), np.zeros(BINS+2)))
            h += histogram[cut]*scale
            variance += histogram[cut]*scale*scale
    density = []
    width = MAX_ENERGY/BINS
    for (category, cut), (h, variance) in sorted(histograms.items()):
        density.append(dict(category=category, fiducial=cut,
            bins=[dict(low_keV=i*width, high_keV=(i+1)*width, counts_per_keV_year=float(h[i+1]/width),
                       error_per_keV_year=float(math.sqrt(variance[i+1])/width)) for i in range(BINS)],
            underflow_per_year=float(h[0]), overflow_per_year=float(h[-1])))
    return dict(windows=windows, categories=list(categories.values()), totals=list(totals.values()),
                density=density, units='windows: counts/year; density: counts/keV/year', boundaries=BOUNDARIES,
                error_convention='Poisson group counts; independent jobs; no assay/geometry uncertainties')
