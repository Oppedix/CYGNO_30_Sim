"""Render existing normalized ROOT spectra and exact-window exports.

This module never normalizes events or fits a published rate. ROOT source
histograms remain counts/bin/year; only cloned display histograms become density.
"""
from pathlib import Path
from .root_io import root_file

from analysis.common.reporting import CATEGORIES, REFERENCE_72, REFERENCE_73, write_table, write_tables


def render(directory, spectra, summary):
    """Report partial coverage visibly; absent contributions are never zero estimates."""
    import ROOT
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetTextFont(42)
    ROOT.gStyle.SetLabelFont(42, 'XYZ')
    ROOT.gStyle.SetTitleFont(42, 'XYZ')
    directory = Path(directory)
    status = write_tables(directory, spectra, summary)
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
