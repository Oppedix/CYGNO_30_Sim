"""Render existing normalized ROOT spectra and exact-window exports.

This module never normalizes events or fits a published rate. ROOT source
histograms remain counts/bin/year; only cloned display histograms become density.
"""
import csv
import json
import math
from pathlib import Path
from .root_io import root_file

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


def render(directory, spectra, summary):
    """Report partial coverage visibly; absent contributions are never zero estimates."""
    import ROOT
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetTextFont(42)
    ROOT.gStyle.SetLabelFont(42, 'XYZ')
    ROOT.gStyle.SetTitleFont(42, 'XYZ')
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
    file = root_file(directory/'NormalizedHisto.root')
    try:
        colors = ('#0072B2','#999999','#56B4E9','#E69F00','#CC79A7','#D55E00','#009E73')
        for cut, figure in ((0,'figure7.5'), (1,'figure7.6')):
            canvas = ROOT.TCanvas('canvas_'+figure, figure, 1800, 1100)
            canvas.SetLeftMargin(.12); canvas.SetRightMargin(.035)
            canvas.SetBottomMargin(.12); canvas.SetTopMargin(.14)
            stack = ROOT.THStack('stack_'+figure, '')
            legend = ROOT.TLegend(.61,.60,.95,.84)
            legend.SetBorderSize(0); legend.SetFillStyle(0); legend.SetTextSize(.025)
            keep = []
            for category, color in zip(CATEGORIES, colors):
                original = file.Get('Categories/'+category+('_cut' if cut else ''))
                if not original:
                    legend.AddEntry(ROOT.nullptr, category+' (missing)', '')
                    continue
                hist = original.Clone('density_'+category+str(cut)); hist.SetDirectory(0)
                hist.Scale(1., 'width')  # actual bin width, including future nonuniform bins
                hist.SetFillColor(ROOT.TColor.GetColor(color)); hist.SetLineColor(ROOT.TColor.GetColor(color))
                stack.Add(hist); keep.append(hist); legend.AddEntry(hist, category, 'f')
            stack.Draw('HIST')
            stack.GetXaxis().SetTitle('Deposited energy [keV]')
            stack.GetYaxis().SetTitle('counts / keV / year')
            stack.GetYaxis().SetTitleOffset(1.25)
            maximum = stack.GetMaximum()
            if maximum > 0:
                canvas.SetLogy()
                positive = [h.GetBinContent(i) for h in keep for i in range(1,h.GetNbinsX()+1) if h.GetBinContent(i)>0]
                stack.SetMinimum(min(positive)*.25); stack.SetMaximum(maximum*20)
            else:
                stack.SetMinimum(0); stack.SetMaximum(1)
            legend.Draw()
            title = ROOT.TLatex(); title.SetNDC(); title.SetTextFont(42)
            title.SetTextSize(.035); title.DrawLatex(.12,.945, 'Internal radioactivity: '+('20 mm fiducial cut' if cut else 'no fiducial cut'))
            title.SetTextSize(.022); title.DrawLatex(.12,.90,status)
            canvas.SaveAs(str(directory/(figure+'.png')))
            canvas.SaveAs(str(directory/(figure+'.pdf')))
            canvas.Close()
    finally:
        file.Close()
