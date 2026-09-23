"""Tables and matplotlib figures from normalized arrays; reference values never scale data."""
import csv
import json
import math
from pathlib import Path

CATEGORIES = ('Camera Lenses', 'Vessel', 'Camera Sensors', 'Cathodes',
              'Resistors', 'GEMs', 'Field Cage')
# Published comparison only: audited transcription in docs/history/BACKGROUND_EXPERIMENT.md.
REFERENCE_72 = {'all': (370000, 22600), 'gt10': (320000, 17700), 'gt10_le400': (330000, 17600)}
REFERENCE_73 = dict(zip(CATEGORIES, ((35,16), (1187,465), (4278,1687),
                                    (9293,196), (12542,810), (30540,1769), (313451,17738))))


def write_table(path, rows):
    with path.open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def write_tables(directory, spectra, summary):
    directory = Path(directory)
    status = f"{summary['mode'].upper()} | {summary['coverage']} contributions | " + (
        'software-complete; physics unvalidated' if summary['complete_matrix'] else 'INCOMPLETE; partial sums only')
    totals = {(x['window'], x['fiducial']): x for x in spectra['totals']}
    categories = {(x['category'], x['window'], x['fiducial']): x for x in spectra['categories']}
    table72, table73 = [], []
    for window, reference in REFERENCE_72.items():
        for cut in (0, 1):
            value = totals.get((window, cut))
            table72.append(dict(window=window, definition=spectra['boundaries'][window], fiducial_mm=20*cut,
                calculated_counts_per_year=value['rate_per_year'] if value else None,
                mc_standard_error=math.sqrt(value['variance_per_year2']) if value else None,
                published_reference_counts_per_year=reference[cut], coverage=summary['coverage'],
                complete_matrix=summary['complete_matrix']))
    for category in CATEGORIES:
        for cut in (0, 1):
            value = categories.get((category, 'all', cut))
            table73.append(dict(category=category, window='all', fiducial_mm=20*cut,
                calculated_counts_per_year=value['rate_per_year'] if value else None,
                mc_standard_error=math.sqrt(value['variance_per_year2']) if value else None,
                published_reference_counts_per_year=REFERENCE_73[category][cut],
                coverage=summary['coverage'], complete_matrix=summary['complete_matrix']))
    write_table(directory/'table7.2.csv', table72)
    write_table(directory/'table7.3.csv', table73)
    notes = ['Reference values are comparisons, never normalization inputs.',
             'Published Table 7.2 no-cut (10,400] exceeds >10; retained as printed.',
             'Errors are Poisson group-count errors, not independent-primary, assay or model errors.',
             'Full range includes histogram underflow/overflow; plots display 0–2000 keV only.',
             'Missing/failed contributions are excluded from partial sums, not assigned zero rates.']
    (directory/'tables.json').write_text(json.dumps(dict(status=status, table7_2=table72, table7_3=table73,
                                                       notes=notes), indent=2)+'\n')
    lines = [status, '', 'Table 7.2 style: calculated counts/year (published reference)']
    for row in table72:
        value = row['calculated_counts_per_year']
        lines.append(f"{row['window']:14s} cut={row['fiducial_mm']:2d} mm: {value if value is not None else 'missing'} ({row['published_reference_counts_per_year']})")
    lines += ['', 'Table 7.3 style: calculated full-range counts/year (published reference)']
    for row in table73:
        value = row['calculated_counts_per_year']
        lines.append(f"{row['category']:16s} cut={row['fiducial_mm']:2d} mm: {value if value is not None else 'missing'} ({row['published_reference_counts_per_year']})")
    lines += ['', *notes]
    (directory/'tables.txt').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines), flush=True)

    return status


def render(directory, spectra, summary):
    directory = Path(directory)
    status = write_tables(directory, spectra, summary)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    colors = ('#0072B2','#999999','#56B4E9','#E69F00','#CC79A7','#D55E00','#009E73')
    for cut, name in ((0, 'figure7.5'), (1, 'figure7.6')):
        fig, ax = plt.subplots(figsize=(12, 7), layout='constrained')
        items = {d['category']: d for d in spectra['density'] if d['fiducial'] == cut}
        bottom = None
        positives = []
        for category, color in zip(CATEGORIES, colors):
            if category not in items:
                ax.plot([], [], color=color, label=category+' (missing)')
                continue
            bins = items[category]['bins']
            edges = [b['low_keV'] for b in bins]+[bins[-1]['high_keV']]
            values = np.array([b['counts_per_keV_year'] for b in bins])
            if bottom is None:
                bottom = np.zeros_like(values)
            ax.stairs(bottom+values, edges, baseline=bottom, fill=True, color=color, label=category)
            bottom += values
            positives.extend(values[values > 0])
        if positives:
            ax.set_yscale('log')
            ax.set_ylim(min(positives)*.25, max(bottom)*20)
        else:
            ax.set_ylim(0, 1)
        ax.set(xlim=(0,2000), xlabel='Deposited energy [keV]', ylabel='counts / keV / year',
               title='Internal radioactivity: '+('20 mm fiducial cut' if cut else 'no fiducial cut'))
        fig.suptitle(status, fontsize=10)
        ax.legend(fontsize=9)
        for extension in ('png', 'pdf'):
            fig.savefig(directory/(name+'.'+extension), dpi=160)
        plt.close(fig)
