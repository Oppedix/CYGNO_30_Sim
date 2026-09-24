"""Small ROOT validation/export adapter; no simulation or physics assumptions."""
import math
from pathlib import Path
from study.source_matrix import require, LAYOUT_MODULE_COUNTS


def root_file(path):
    import ROOT
    ROOT.gROOT.SetBatch(True)
    file = ROOT.TFile.Open(str(path), 'READ')
    require(bool(file) and not file.IsZombie() and not file.TestBit(ROOT.TFile.kRecovered),
            f'Invalid or recovered ROOT file: {path}')
    return file


def identity(file, expected, processed=False):
    tree = file.Get('RunMetadata')
    require(bool(tree) and tree.InheritsFrom('TTree') and tree.GetEntries() == 1,
            'Need exactly one RunMetadata row')
    tree.GetEntry(0)
    for name, key in [('GeometryHash', 'geometry_hash'), ('Layout', 'layout'),
                      ('DetectorModel', 'model'), ('SourcePolicy', 'source_policy')]:
        leaf = tree.GetLeaf(name)
        require(bool(leaf) and leaf.GetTypeName() == 'Char_t' and
                leaf.GetValueString() == expected[key], f'Raw identity mismatch: {name}')
        if processed:
            marker = file.Get({'GeometryHash': 'CygnoGeometry', 'Layout': 'CygnoLayout',
                               'DetectorModel': 'CygnoDetectorModel', 'SourcePolicy': 'CygnoSourcePolicy'}[name])
            require(bool(marker) and marker.InheritsFrom('TNamed') and
                    marker.GetTitle() == expected[key], f'Processed identity mismatch: {name}')


def inspect_raw(path, expected, requested):
    file = root_file(path)
    try:
        identity(file, expected)
        tree = file.Get('RunAccounting')
        require(bool(tree) and tree.InheritsFrom('TTree') and tree.GetEntries() == 1,
                'Missing or multiple end-of-run accounting records')
        tree.GetEntry(0)
        values = {}
        for name in ('RunID', 'RequestedEvents', 'GeneratedPrimaries', 'ProcessedEvents', 'AbortedEvents'):
            leaf = tree.GetLeaf(name)
            require(bool(leaf) and leaf.GetTypeName() == 'Int_t', f'Invalid accounting field {name}')
            values[name] = int(leaf.GetValue())
        require(values == dict(RunID=0, RequestedEvents=requested, GeneratedPrimaries=requested,
                               ProcessedEvents=requested, AbortedEvents=0),
                f'Incomplete/aborted run: {values}; requested {requested}')
        hits = file.Get('Hits')
        require(bool(hits) and hits.InheritsFrom('TTree'), 'Missing Hits (zero rows are allowed)')
        # Validate schema even for a no-hit run, independent of processing.
        fields = dict(EventNumber='Int_t', ParticleName='Char_t', ParticleID='Int_t',
                      ParticleTag='Int_t', ParentID='Int_t', x_hits='Double_t',
                      y_hits='Double_t', z_hits='Double_t', EnergyDeposit='Double_t',
                      VolumeNumber='Int_t', Nucleus='Char_t', ProcessType='Char_t')
        for name, kind in fields.items():
            leaf = hits.GetLeaf(name)
            require(bool(leaf) and leaf.GetTypeName() == kind, f'Invalid Hits field {name}')
        for index in range(hits.GetEntries()):
            require(hits.GetEntry(index) > 0, 'Unreadable Hits row')
            require(0 <= hits.GetLeaf('EventNumber').GetValue() < requested, 'Invalid event ID')
        return values | {'hit_rows': int(hits.GetEntries()), 'chain_validity': 'unvalidated'}
    finally:
        file.Close()


def inspect_processed(path, expected):
    file = root_file(path)
    try:
        identity(file, expected, processed=True)
        require(file.Get('CygnoBuildSource') and file.Get('CygnoBuildSource').GetTitle() == expected['source_hash'],
                'Stale processor build')
        tree = file.Get('elabHits')
        require(bool(tree) and tree.InheritsFrom('TTree'), 'Missing processed tree')
        for row in tree:
            lengths = [len(getattr(row, field)) for field in
                       ('EDep_Out', 'VolNnum_Out', 'X_Vertex', 'Y_Vertex', 'Z_Vertex')]
            require(lengths[0] > 0 and len(set(lengths)) == 1, 'Malformed processed vectors')
            require(all(math.isfinite(x) for field in ('EDep_Out', 'X_Vertex', 'Y_Vertex', 'Z_Vertex')
                        for x in getattr(row, field)), 'Nonfinite processed values')
            require(all(math.isfinite(x) and x == int(x) and 0 <= x < 2*LAYOUT_MODULE_COUNTS[expected['layout']] for x in row.VolNnum_Out),
                    'Invalid processed gas copy')
        return int(tree.GetEntries())
    finally:
        file.Close()


def export_spectra(path, rows, expected_source_hash=None):
    """Exact window counts/rates and density display; flows stay separate."""
    file = root_file(path)
    try:
        if expected_source_hash is not None:
            require(file.Get('CygnoBuildSource') and file.Get('CygnoBuildSource').GetTitle() == expected_source_hash,
                    'Stale plotter build')
        tree = file.Get('ExactEnergyWindows')
        require(bool(tree) and tree.GetEntries() == 12*len(rows), 'Incomplete exact energy windows')
        mapping = {row['id']: row['category'] for row in rows}
        windows, categories, totals = [], {}, {}
        seen = set()
        names = {'all', 'gt10', 'gt10_le400', 'underflow', 'in_range', 'overflow'}
        for row in tree:
            item = dict(contribution=str(row.Contribution), window=str(row.Window),
                        fiducial=int(row.Fiducial), count=int(row.Count),
                        rate_per_year=float(row.RatePerYear), variance_per_year2=float(row.VariancePerYear2))
            key = (item['contribution'], item['window'], item['fiducial'])
            require(key not in seen and key[0] in mapping and key[1] in names and key[2] in (0, 1),
                    'Invalid/duplicate window row')
            require(item['count'] >= 0 and all(math.isfinite(item[k]) and item[k] >= 0
                    for k in ('rate_per_year', 'variance_per_year2')), 'Invalid window rate')
            seen.add(key); windows.append(item)
            for target, label in ((categories, mapping[key[0]]), (totals, 'total')):
                aggregate = target.setdefault((label, key[1], key[2]),
                                              dict(category=label, window=key[1], fiducial=key[2],
                                                   count=0, rate_per_year=0., variance_per_year2=0.))
                for field in ('count', 'rate_per_year', 'variance_per_year2'):
                    aggregate[field] += item[field]
        density = []
        for category in sorted(set(mapping.values())):
            for cut in (0, 1):
                hist = file.Get('Categories/'+category+('_cut' if cut else ''))
                require(bool(hist), 'Missing category histogram')
                bins = [dict(low_keV=hist.GetBinLowEdge(i), high_keV=hist.GetBinLowEdge(i+1),
                             counts_per_keV_year=hist.GetBinContent(i)/hist.GetBinWidth(i),
                             error_per_keV_year=hist.GetBinError(i)/hist.GetBinWidth(i))
                        for i in range(1, hist.GetNbinsX()+1)]
                density.append(dict(category=category, fiducial=cut, bins=bins,
                                    underflow_per_year=hist.GetBinContent(0),
                                    overflow_per_year=hist.GetBinContent(hist.GetNbinsX()+1)))
        return dict(windows=windows, categories=list(categories.values()), totals=list(totals.values()),
                    density=density, units='windows: counts/year; density: counts/keV/year',
                    boundaries={'all': 'all finite energies, including underflow and overflow',
                                'gt10': 'E > 10 keV, no upper limit', 'gt10_le400': '10 < E <= 400 keV',
                                'underflow': 'E < 0 keV', 'in_range': '0 <= E < 2000 keV',
                                'overflow': 'E >= 2000 keV'},
                    error_convention='Poisson group counts; independent jobs; no assay/geometry uncertainties')
    finally:
        file.Close()
