// External-only entry point: the original single-campaign analyzer is included unchanged.
#define main AnalyzeExternalSingle
#include "../analysis/common_c++/AnalyzeExternal.cpp"
#undef main
#include <sys/wait.h>
#include <unistd.h>
#ifndef CYGNO_MERGE_SCRIPT
#define CYGNO_MERGE_SCRIPT "external/merge/merge.py"
#endif

void childSuccess(pid_t pid) {
  require(pid>0,"Cannot fork analysis/validation process");
  int status=0;require(waitpid(pid,&status,0)==pid && WIFEXITED(status) && WEXITSTATUS(status)==0,
                       "Input validation/analysis failed; inspect the diagnostics and retained .partial directory");
}
Long64_t exactCount(const JSONNode& node) {
  const double x=number(node);require(x>0 && x<=9007199254740991. && x==std::floor(x),"Invalid joined count");return Long64_t(x);
}
int main(int argc,char** argv) try {
  require(argc==3,"Usage: AnalyzeExternal CAMPAIGN_DIR NEW_OUTPUT_DIR");
  const auto source=fs::canonical(argv[1]);auto doc=json(source/"campaign.json");const auto& joined=doc->rootnode();
  if(!joined.has_child("external_join_version"))return AnalyzeExternalSingle(argc,argv);
  require(integer(joined["external_join_version"])==1 && joined["status"].val()=="complete","Invalid external join");
  const auto output=fs::weakly_canonical(argv[2]);const fs::path staging=output.string()+".partial";
  require(!within(output,source) && !fs::exists(output) && !fs::exists(staging),"Use a new output outside campaign");
  const auto& members=joined["members"];
  for(unsigned i=0;i<members.num_children();++i) {
    const auto input=fs::canonical(members.child(i)["path"].val());
    require(!within(output,input) && !within(staging,input),"Output must be outside all original inputs");
  }
  // Recheck every saved checksum and manifest before reading ROOT; no shell interpolation.
  auto pid=fork();
  if(pid==0) {
    execlp("python3","python3",CYGNO_MERGE_SCRIPT,"--output",source.c_str(),"--verify",static_cast<char*>(nullptr));
    _exit(127);
  }
  childSuccess(pid);
  gROOT->SetBatch(true);fs::create_directories(staging/"members");
  std::array<std::array<Long64_t,1002>,4> counts{};
  std::array<Long64_t,4> positive{},window{};
  const std::array<const char*,4> channels={"total","electromagnetic","charged_hadron","other"};
  const auto generated=exactCount(joined["generated_primaries"]);
  Long64_t checked=0;
  for(unsigned i=0;i<members.num_children();++i) {
    const auto input=members.child(i)["path"].val();const auto part=(staging/"members"/std::to_string(i)).string();
    checked+=exactCount(members.child(i)["campaign"]["accounting"]["GeneratedPrimaries"]);
    pid=fork();
    if(pid==0) {
      char* args[]={argv[0],const_cast<char*>(input.c_str()),const_cast<char*>(part.c_str())};
      const int result=AnalyzeExternalSingle(3,args);_exit(result);
    }
    childSuccess(pid);
    std::ifstream spectra(fs::path(part)/"spectra.tsv"),windows(fs::path(part)/"windows.tsv");
    std::string line;std::getline(spectra,line);std::getline(windows,line);
    for(int ch=0;ch<4;++ch) {
      for(int bin=0;bin<1002;++bin) {
        std::string name;int index=-1;Long64_t n=-1;double annual=0,variance=0;
        require(bool(spectra>>name>>index>>n>>annual>>variance) && name==channels[ch] && index==bin && n>=0 && n<=generated,"Invalid member count table");
        require(counts[ch][bin]<=generated-n,"Joined count overflow");counts[ch][bin]+=n;
      }
      std::string name;Long64_t p=-1,w=-1;double py=0,wy=0;
      require(bool(windows>>name>>p>>w>>py>>wy) && name==channels[ch] && w>=0 && p>=w && p<=generated,"Invalid member windows");
      require(positive[ch]<=generated-p && window[ch]<=generated-w,"Joined window overflow");positive[ch]+=p;window[ch]+=w;
    }
  }
  require(checked==generated,"Joined denominator mismatch");
  const auto& compat=joined["compatibility"];const auto& cfg=compat["config"];
  const double incident=number(compat["incident_rate_s"]),scale=incident*31536000/generated;
  require(incident>0 && std::isfinite(scale),"Invalid joined normalization");
  std::ofstream tsv(staging/"spectra.tsv"),windows(staging/"windows.tsv"),summary(staging/"summary.txt");
  tsv<<std::setprecision(17)<<"channel\tbin\tMC_events\tannual_events\tannual_variance\n";
  windows<<std::setprecision(17)<<"channel\tpositive_MC\tgt10_le400_MC\tpositive_per_year\tgt10_le400_per_year\n";
  summary<<std::setprecision(17)<<"External environmental primary-event analysis\n"<<cfg["scientific_status"].val()<<"\n"
         <<"campaign="<<source<<"\nfingerprint="<<joined["fingerprint"].val()<<"\nlayout="<<cfg["layout"].val()
         <<"\nparticle="<<cfg["particle"].val()<<"\nshield="<<cfg["shield"].val()<<"\nflux_convention="<<cfg["flux_convention"].val()
         <<"\nsource_radius_mm="<<number(compat["radius_mm"])<<"\nincident_rate_s="<<incident
         <<"\ngenerated_primaries="<<generated<<"\nscale_per_year="<<scale<<"\n"
         <<"Deposited keV, no quenching/reconstruction; each primary counted once per channel.\n"
         <<"Positive deposits only; exact window 10<E<=400 keV; overflow E>=1000 keV.\n"
         <<"Poisson primary-event MC variance; flux/model uncertainties excluded.\n"
         <<"Logical external join; immutable original event namespaces retained.\n";
  TFile result((staging/"analysis.root").c_str(),"CREATE");require(!result.IsZombie(),"Cannot create ROOT report");
  std::array<std::unique_ptr<TH1D>,4> hist;
  TCanvas canvas("external_join","External deposited energy",1100,750);TLegend legend(.62,.65,.89,.88);
  bool nonempty=false;double maximum=0;const std::array<int,4> colors={kBlack,kRed+1,kGreen+2,kBlue+1};
  for(int ch=0;ch<4;++ch) {
    hist[ch]=std::make_unique<TH1D>(channels[ch],"External scenario;Deposited energy [keV];primary events / keV / year",1000,0,1000);
    hist[ch]->SetDirectory(nullptr);hist[ch]->SetStats(false);hist[ch]->SetLineColor(colors[ch]);hist[ch]->SetLineWidth(2);
    Long64_t sum=0;
    for(int bin=0;bin<1002;++bin) {
      const auto n=counts[ch][bin];sum+=n;
      tsv<<channels[ch]<<'\t'<<bin<<'\t'<<n<<'\t'<<n*scale<<'\t'<<n*scale*scale<<'\n';
      hist[ch]->SetBinContent(bin,n*scale);hist[ch]->SetBinError(bin,std::sqrt(double(n))*scale);
    }
    require(sum==positive[ch] && sum<=generated,"Joined positive count mismatch");
    hist[ch]->SetEntries(positive[ch]);hist[ch]->Write();
    windows<<channels[ch]<<'\t'<<positive[ch]<<'\t'<<window[ch]<<'\t'<<positive[ch]*scale<<'\t'<<window[ch]*scale<<'\n';
    nonempty=nonempty || hist[ch]->Integral()>0;maximum=std::max(maximum,hist[ch]->GetMaximum());
    legend.AddEntry(hist[ch].get(),channels[ch],"l");
  }
  hist[0]->SetMinimum(nonempty ? scale*.1 : 0.);hist[0]->SetMaximum(nonempty ? maximum*10 : 1.);canvas.SetLogy(nonempty);
  for(int ch=0;ch<4;++ch)hist[ch]->Draw(ch==0 ? "HIST" : "HIST SAME");legend.Draw();
  TNamed("CampaignFingerprint",joined["fingerprint"].val().c_str()).Write();
  TNamed("ScientificStatus",cfg["scientific_status"].val().c_str()).Write();TParameter<double>("ScalePerYear",scale).Write();
  result.Write();require(!result.TestBit(TFile::kWriteError),"ROOT write failed");result.Close();
  canvas.SaveAs((staging/"spectra.png").c_str());canvas.SaveAs((staging/"spectra.pdf").c_str());
  tsv.close();windows.close();summary.close();require(bool(tsv) && bool(windows) && bool(summary),"Text export failed");
  require(fs::file_size(staging/"spectra.png")>0 && fs::file_size(staging/"spectra.pdf")>0,"Figure export failed");
  fs::copy_file(source/"campaign.json",staging/"joined-campaign.json");fs::rename(staging,output);return 0;
} catch(const std::exception& e) {std::cerr<<"External joined analysis: "<<e.what()<<'\n';return 1;}
