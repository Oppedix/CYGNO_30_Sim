// ROOT-only primary-event analysis. No Geant4 or Python runtime required.
#include <RooFit/Detail/JSONInterface.h>
#include <TFile.h>
#include <TTree.h>
#include <TLeafC.h>
#include <TH1D.h>
#include <TCanvas.h>
#include <TLegend.h>
#include <TNamed.h>
#include <TParameter.h>
#include <TROOT.h>
#include <array>
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
namespace fs=std::filesystem;
using RooFit::Detail::JSONTree;
using RooFit::Detail::JSONNode;
#ifdef __FAST_MATH__
#error "Compile without fast math"
#endif
void require(bool ok,const std::string& message) {if(!ok)throw std::runtime_error(message);}
std::unique_ptr<JSONTree> json(const fs::path& path) {
  std::ifstream in(path);require(bool(in),"Cannot read "+path.string());
  std::ostringstream text;text<<in.rdbuf();return JSONTree::create(text.str());
}
double number(const JSONNode& node) {
  const auto x=node.val_double();require(std::isfinite(x),"Nonfinite metadata");return x;
}
int integer(const JSONNode& node) {
  const auto x=number(node);require(x>=0 && x<=2147483647 && x==std::floor(x),"Invalid metadata integer");return int(x);
}
bool within(const fs::path& path,const fs::path& root) {
  const auto relative=path.lexically_relative(root);
  return !relative.empty() && *relative.begin()!="..";
}
fs::path inside(const fs::path& root,const std::string& name) {
  const fs::path p(name);require(!name.empty() && !p.is_absolute() && name.find('\\')==std::string::npos,"Unsafe path");
  for(const auto& part:p)require(part!="..","Path traversal");
  const auto result=fs::canonical(root/p);require(within(result,root),"Path escapes campaign");return result;
}
TTree& tree(TFile& file,const char* name,bool one=false) {
  auto* t=dynamic_cast<TTree*>(file.Get(name));require(t && (!one || t->GetEntries()==1),std::string("Invalid tree: ")+name);
  t->SetBranchStatus("*",false);return *t;
}
TLeaf* branch(TTree& t,const char* name,const char* type,void* address=nullptr) {
  auto* l=t.GetLeaf(name);
  require(l && std::string(l->GetTypeName())==type && !l->GetLeafCount() &&
          (std::string(type)=="Char_t" || l->GetLenStatic()==1),std::string("Invalid branch: ")+name);
  t.SetBranchStatus(name,true);
  if(address)require(t.SetBranchAddress(name,address)>=0,"Cannot bind branch");return l;
}
std::string text(TTree& t,const char* name,Long64_t row=0) {
  auto* l=static_cast<TLeafC*>(branch(t,name,"Char_t"));require(t.GetEntry(row)>0,"Cannot read text row");return l->GetValueString();
}
int channel(const std::string& particle) {
  if(particle=="e-" || particle=="e+")return 1;
  static const std::regex ion("[A-Z][a-z]?[0-9]+(\\[.*\\])?");
  if(particle=="proton" || particle=="deuteron" || particle=="triton" || particle=="alpha" || particle=="He3" || std::regex_match(particle,ion))return 2;
  return 3;
}
int main(int argc,char** argv) try {
  require(argc==3,"Usage: AnalyzeExternal CAMPAIGN_DIR NEW_OUTPUT_DIR");
  gROOT->SetBatch(true);
  const auto source=fs::canonical(argv[1]);const auto output=fs::weakly_canonical(argv[2]);
  const fs::path staging=output.string()+".partial";
  require(!within(output,source) && !fs::exists(output) && !fs::exists(staging),"Use a new output outside campaign");
  auto campaign=json(source/"campaign.json");const auto& c=campaign->rootnode();
  require(integer(c["external_campaign_version"])==1 && c["status"].val()=="complete","Not a complete external campaign");
  const auto& id=c["identity"];const auto& cfg=id["config"];const auto& env=id["environment"];
  auto config=json(source/"config.json");
  std::ostringstream a,b;cfg.writeJSON(a);config->rootnode().writeJSON(b);
  require(a.str()==b.str(),"Config snapshot mismatch");
  require(cfg["mode"].val()=="external" && (cfg["output_mode"].val()=="compact" || cfg["output_mode"].val()=="both"),"Native analysis requires external compact representation");
  const int requested=integer(cfg["primaries"]);require(requested>0,"Invalid event count");
  const auto layout=cfg["layout"].val();
  require(layout=="legacy-25x3" || layout=="cygno-11x7-v1" || layout=="cygno-5x5x3-v1","Unknown layout");
  require(cfg["shield"].val()=="none" || cfg["shield"].val()=="copper20","Unknown shield");
  require(cfg["particle"].val()=="gamma" || cfg["particle"].val()=="neutron","Unknown primary");
  const auto attempt=inside(source,c["attempt"].val());const auto data=inside(attempt,c["data_path"].val());
  auto attemptRecord=json(attempt/"manifest.json");
  std::ostringstream recorded,current;c.writeJSON(current);attemptRecord->rootnode().writeJSON(recorded);
  require(recorded.str()==current.str(),"Attempt/campaign manifest mismatch");
  auto geometry=json(source/"geometry.json");const auto& geo=geometry->rootnode();
  require(geo["geometry_hash"].val()==env["geometry_hash"].val() && geo["source_hash"].val()==env["source_hash"].val() &&
          geo["layout"].val()==layout,"Geometry snapshot mismatch");
  const int gasCount=layout=="cygno-11x7-v1" ? 154 : 150;
  require(geo["gas_centers_mm"].num_children()==unsigned(gasCount),"Invalid gas map");
  TFile file(data.c_str(),"READ");require(!file.IsZombie(),"Cannot open compact ROOT file");
  auto& metadata=tree(file,"RunMetadata",true);
  require(text(metadata,"SourcePolicy")=="environmental-surface-v1" && text(metadata,"DetectorModel")=="cygno-300elj-v2" &&
          text(metadata,"Layout")==layout && text(metadata,"GeometryHash")==env["geometry_hash"].val(),"Mixed scientific identity");
  auto& format=tree(file,"OutputMetadata",true);int version=0;branch(format,"OutputSchemaVersion","Int_t",&version);
  require(text(format,"OutputFormat")==cfg["output_mode"].val() && version==1 && text(format,"CompactProcessingVersion")=="external-track-volumes-v1" &&
          text(format,"TimingDefinition")=="pre-step global time / ns; Geant4 event-relative, not inter-event time","Wrong compact convention");
  auto& simulation=tree(file,"SimulationMetadata",true);double radius=0;branch(simulation,"SourceRadius_mm","Double_t",&radius);
  require(text(simulation,"Mode")=="external" && text(simulation,"Shielding")==cfg["shield"].val() &&
          text(simulation,"PhysicsList")=="QGSP_BIC_HP_EMZ" && text(simulation,"SourceHash")==env["source_hash"].val() &&
          text(simulation,"ExternalGeometryHash")==id["external_geometry_hash"].val() && radius==number(id["source_radius_mm"]) && radius>0,
          "Mixed external transport identity");
  auto& accounting=tree(file,"RunAccounting",true);
  int run=0,generated=0,processed=0,aborted=0,expected=0;
  branch(accounting,"RunID","Int_t",&run);branch(accounting,"GeneratedPrimaries","Int_t",&generated);
  branch(accounting,"ProcessedEvents","Int_t",&processed);branch(accounting,"RequestedEvents","Int_t",&expected);branch(accounting,"AbortedEvents","Int_t",&aborted);
  require(accounting.GetEntry(0)>0 && run==0 && generated==requested && processed==generated && expected==generated && aborted==0,"Incomplete primary accounting");
  require(integer(c["accounting"]["RunID"])==run && integer(c["accounting"]["GeneratedPrimaries"])==generated &&
          integer(c["accounting"]["ProcessedEvents"])==processed && integer(c["accounting"]["RequestedEvents"])==expected &&
          integer(c["accounting"]["AbortedEvents"])==aborted,"Manifest/ROOT accounting mismatch");
  const double flux=number(cfg["flux_cm2_s"]);require(flux>0,"Invalid environmental flux");
  const auto convention=cfg["flux_convention"].val();require(convention=="scalar" || convention=="inward_current","Ambiguous flux convention");
  const double r=radius/10.;const double incident=flux*(4*std::acos(-1.)*(r*r))/(convention=="scalar" ? 4.:1.);
  require(std::abs(number(c["incident_rate_s"])-incident)<1e-12*incident,"Flux normalization mismatch");
  const double scale=incident*31536000/generated;
  std::array<std::array<Long64_t,1002>,4> counts{};
  std::array<Long64_t,4> positive{},window{};
  std::array<double,4> energy{};
  auto flush=[&]() {
    for(int ch=0;ch<4;++ch) {
      require(std::isfinite(energy[ch]),"Event energy overflow");
      if(energy[ch]<=0)continue;
      const int bin=energy[ch]>=1000 ? 1001 : 1+int(energy[ch]);
      ++counts[ch][bin];++positive[ch];window[ch]+=energy[ch]>10 && energy[ch]<=400;
    }
    energy={};
  };
  auto& groups=tree(file,"Groups");auto& volumes=tree(file,"GroupVolumes");
  int event=0,index=0,nvol=0,ntrack=0,nstep=0;
  branch(groups,"EventNumber","Int_t",&event);branch(groups,"GroupIndex","Int_t",&index);
  auto* particle=static_cast<TLeafC*>(branch(groups,"ParticleName","Char_t"));
  branch(groups,"VolumeCount","Int_t",&nvol);branch(groups,"TrackCount","Int_t",&ntrack);branch(groups,"StepCount","Int_t",&nstep);
  int vevent=0,vindex=0,order=0,volume=0;double deposit=0,x=0,y=0,z=0,time=0;
  branch(volumes,"EventNumber","Int_t",&vevent);branch(volumes,"GroupIndex","Int_t",&vindex);
  branch(volumes,"VolumeOrder","Int_t",&order);branch(volumes,"VolumeNumber","Int_t",&volume);
  branch(volumes,"EnergyDeposit","Double_t",&deposit);branch(volumes,"x_first","Double_t",&x);
  branch(volumes,"y_first","Double_t",&y);branch(volumes,"z_first","Double_t",&z);branch(volumes,"FirstHitTime_ns","Double_t",&time);
  Long64_t cursor=0;int lastEvent=-1,nextIndex=0;
  for(Long64_t i=0;i<groups.GetEntries();++i) {
    require(groups.GetEntry(i)>0 && event>=0 && event<generated && event>=lastEvent,"Invalid group event order");
    if(event!=lastEvent) {flush();nextIndex=0;lastEvent=event;}
    require(index==nextIndex++ && ntrack==1 && nvol>0 && nstep>=nvol,"Invalid track group");
    const std::string name=particle->GetValueString();require(!name.empty(),"Missing particle identity");const int ch=channel(name);
    std::set<int> seen;
    for(int j=0;j<nvol;++j) {
      require(cursor<volumes.GetEntries() && volumes.GetEntry(cursor++)>0,"Truncated group volumes");
      require(vevent==event && vindex==index && order==j && volume>=0 && volume<gasCount && seen.insert(volume).second,"Invalid group-volume key");
      require(std::isfinite(deposit) && deposit>=0 && std::isfinite(x) && std::isfinite(y) && std::isfinite(z) && std::isfinite(time),"Invalid volume payload");
      energy[0]+=deposit*1000;energy[ch]+=deposit*1000;
    }
  }
  flush();require(cursor==volumes.GetEntries(),"Orphan group volumes");
  file.Close();
  const std::array<const char*,4> channels={"total","electromagnetic","charged_hadron","other"};
  fs::create_directories(staging);
  std::ofstream tsv(staging/"spectra.tsv"),windows(staging/"windows.tsv"),summary(staging/"summary.txt");
  tsv<<std::setprecision(17)<<"channel\tbin\tMC_events\tannual_events\tannual_variance\n";
  windows<<std::setprecision(17)<<"channel\tpositive_MC\tgt10_le400_MC\tpositive_per_year\tgt10_le400_per_year\n";
  summary<<std::setprecision(17)<<"External environmental primary-event analysis\n"<<cfg["scientific_status"].val()<<"\n"
         <<"campaign="<<source<<"\nfingerprint="<<c["fingerprint"].val()<<"\nlayout="<<layout<<"\nparticle="<<cfg["particle"].val()
         <<"\nshield="<<cfg["shield"].val()<<"\nflux_convention="<<convention<<"\nsource_radius_mm="<<radius<<"\nincident_rate_s="<<incident
         <<"\ngenerated_primaries="<<generated<<"\nscale_per_year="<<scale<<"\n"
         <<"Deposited keV, no quenching/reconstruction; each primary counted once per channel.\n"
         <<"Positive deposits only; exact window 10<E<=400 keV; overflow E>=1000 keV.\n"
         <<"Poisson primary-event MC variance; flux/model uncertainties excluded.\n"
         <<"Fast ROOT checks; run external Python validation for full checksums and track relationships.\n";
  TFile result((staging/"analysis.root").c_str(),"CREATE");require(!result.IsZombie(),"Cannot create ROOT report");
  std::array<std::unique_ptr<TH1D>,4> hist;
  TCanvas canvas("external","External deposited energy",1100,750);TLegend legend(.62,.65,.89,.88);
  bool nonempty=false;double maximum=0.;
  const std::array<int,4> colors={kBlack,kRed+1,kGreen+2,kBlue+1};
  for(int ch=0;ch<4;++ch) {
    hist[ch]=std::make_unique<TH1D>(channels[ch],"External scenario;Deposited energy [keV];primary events / keV / year",1000,0,1000);
    hist[ch]->SetDirectory(nullptr);hist[ch]->SetStats(false);hist[ch]->SetLineColor(colors[ch]);hist[ch]->SetLineWidth(2);
    for(int bin=0;bin<1002;++bin) {
      const auto n=counts[ch][bin];tsv<<channels[ch]<<'\t'<<bin<<'\t'<<n<<'\t'<<n*scale<<'\t'<<n*scale*scale<<'\n';
      hist[ch]->SetBinContent(bin,n*scale);hist[ch]->SetBinError(bin,std::sqrt(double(n))*scale);
    }
    hist[ch]->SetEntries(positive[ch]);hist[ch]->Write();
    windows<<channels[ch]<<'\t'<<positive[ch]<<'\t'<<window[ch]<<'\t'<<positive[ch]*scale<<'\t'<<window[ch]*scale<<'\n';
    nonempty=nonempty || hist[ch]->Integral()>0;
    maximum=std::max(maximum,hist[ch]->GetMaximum());
    legend.AddEntry(hist[ch].get(),channels[ch],"l");
  }
  hist[0]->SetMinimum(nonempty ? scale*.1 : 0.);hist[0]->SetMaximum(nonempty ? maximum*10 : 1.);
  canvas.SetLogy(nonempty);
  for(int ch=0;ch<4;++ch)hist[ch]->Draw(ch==0 ? "HIST" : "HIST SAME");
  legend.Draw();
  TNamed("CampaignFingerprint",c["fingerprint"].val().c_str()).Write();
  TNamed("ScientificStatus",cfg["scientific_status"].val().c_str()).Write();
  TParameter<double>("ScalePerYear",scale).Write();
  result.Write();require(!result.TestBit(TFile::kWriteError),"ROOT write failed");result.Close();
  canvas.SaveAs((staging/"spectra.png").c_str());canvas.SaveAs((staging/"spectra.pdf").c_str());
  tsv.close();windows.close();summary.close();require(bool(tsv) && bool(windows) && bool(summary),"Text export failed");
  require(fs::file_size(staging/"spectra.png")>0 && fs::file_size(staging/"spectra.pdf")>0,"Figure export failed");
  fs::rename(staging,output);return 0;
} catch(const std::exception& e) {std::cerr<<"External analysis: "<<e.what()<<'\n';return 1;}
