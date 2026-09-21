#include "DetectorGeometry.hh"
#include "Normalization.hh"
// ROOT post-processing: normalize elabHits spectra using explicitly configured masses,
// activities and generated-event counts, then apply the existing fiducial cuts.
// These inputs and the reconstructed geometry require review before a new study.
#include <iostream>
#include <cstring>
#include <map>
#include "TFile.h"
#include "TTree.h"
#include "TH1D.h"
#include "TH2D.h"
#include "THStack.h"
#include "TVector3.h"

bool isWithin(const std::map<Int_t,TVector3>& aMap,const Double_t x,const Double_t y,const Double_t z,const Int_t Volnum);
TVector3* RelativePos(const std::map<Int_t,TVector3>& aMap,const Double_t x,const Double_t y,const Double_t z,const Int_t Volnum);

int main(int argc, char** argv) try {
  if (argc != 2) { std::cerr << "Usage: " << argv[0] << " study.tsv\n"; return 1; }
  const auto settings = ReadNormalization(argv[1]);
  auto ElementMass = settings.masses;
  auto Contaminant = settings.activities;
  auto NEvents = settings.events;

  //Build centroid detector map for fiducialization
  std::map<Int_t,TVector3> VolumeMap;
  BuildDetectorMap(VolumeMap);

  //declare tree variables
  Int_t evNumber;
  std::string* PartName = nullptr;
  std::vector<double>* EDep=nullptr;
  std::vector<double>* VolNum=nullptr;
  std::string* Nucleus= nullptr;
  std::vector<double>* X_Vertex=nullptr;
  std::vector<double>* Y_Vertex=nullptr;
  std::vector<double>* Z_Vertex=nullptr;
  
  TFile* f;
  TTree* tree;

  TH1D* temp_histo;
  TH1D* temp_histocut;
  
  std::vector<TH1D*> Histo;
  std::vector<TH1D*> HistoCut;

  std::multimap<double_t,TH1D*> IntegralMap;
  std::multimap<double_t,TH1D*> IntegralMap_cut;
  
  Double_t totEdep=0;

  Int_t counter=0;

  TFile* outDef = new TFile("NormalizedHisto.root","recreate");

  /*
  TTree* pos_tree = new TTree("pos_tree","pos_tree");

  Double_t relX,relY,relZ,EDepPart;
  pos_tree->Branch("relX",&relX,"relX/D");
  pos_tree->Branch("relY",&relY,"relY/D");
  pos_tree->Branch("relZ",&relZ,"relZ/D");
  pos_tree->Branch("EDep",&EDepPart,"EDep/D");
  */

  TVector3* a;
  TH2D* hposXY = new TH2D("XYPos","XYPos",1300,-260,260,2300,-410,410);
  TH2D* hposYZ = new TH2D("YZPos","YZPos",2300,-410,410,1300,-550,550);
  
  for(auto& component: ElementMass){ //for components in the map Element Mass
    for(auto& val : Contaminant[component.first]){// for val (that ia map) that get for each detector component the map with <nuclide,contamination>  

      std::cout << "Mass of " << component.first << " is " << component.second << " Kg with contamination of \t" << val.first
		<<" equal to \t" << val.second <<" Bq/Kg nEvents: \t" << NEvents[component.first][val.first] <<"\n";
      
      f= TFile::Open(settings.files.at(component.first).at(val.first).c_str(),"r");
      if (!f || f->IsZombie()) throw std::runtime_error("Cannot open configured input file");
      std::cout << "file " << Form("elab_%s_%s_t0.root", (component.first).c_str(), (val.first).c_str()) << "\n";

      tree = (TTree*)f->Get("elabHits");
      if (!tree) throw std::runtime_error("Missing elabHits tree");

      tree->SetBranchAddress("evNumber",&evNumber);
      tree->SetBranchAddress("PartName",&PartName);
      tree->SetBranchAddress("EDep_Out",&EDep);
      tree->SetBranchAddress("VolNnum_Out",&VolNum);
      tree->SetBranchAddress("Nucleus",&Nucleus);
      tree->SetBranchAddress("X_Vertex",&X_Vertex);
      tree->SetBranchAddress("Y_Vertex",&Y_Vertex);
      tree->SetBranchAddress("Z_Vertex",&Z_Vertex);

      temp_histo = new TH1D(Form("%s_%s",(component.first).c_str(), (val.first).c_str() ), Form("%s_%s",(component.first).c_str(), (val.first).c_str() ),1200,0,2000);
      temp_histocut = new TH1D(Form("%s_%s_cut",(component.first).c_str(), (val.first).c_str() ), Form("%s_%s_cut",(component.first).c_str(), (val.first).c_str() ),1200,0,2000);
      
      for(int i=0;i< tree->GetEntries();i++){
	tree->GetEntry(i);
	
	if(i%40000 == 0) std::cout << i << "/" << tree->GetEntries()<< std::endl;
	
	if(std::strcmp((*PartName).c_str(),"e+")==0 || std::strcmp((*PartName).c_str(),"e-")==0 ){

	  for(int j=0; j<(*EDep).size();j++ ){
	    totEdep+=(*EDep)[j]*1000;	    
	  }//chiudo for on vector

	  if(isWithin( VolumeMap,(*X_Vertex)[0],(*Y_Vertex)[0],(*Z_Vertex)[0],(*VolNum)[0] )){
	    temp_histocut->Fill( totEdep );
	  }//chiudo if within the volume  

	  if(totEdep>10){

	    a=RelativePos(VolumeMap,(*X_Vertex)[0],(*Y_Vertex)[0],(*Z_Vertex)[0],(*VolNum)[0]);
	    
	    hposXY->Fill(a->X(),a->Y());
	    hposYZ->Fill(a->Y(),a->Z());
            delete a;

	  }
	  
	  temp_histo->Fill(totEdep); 
	  totEdep=0;
	  
	}//chiudo if on e-	
	
      }//tree over entries
      
      temp_histo->Sumw2();
      temp_histocut->Sumw2();
      
      temp_histo->Scale( val.second*component.second*60*60*24*365/NEvents[component.first][val.first] );
      temp_histocut->Scale( val.second*component.second*60*60*24*365/NEvents[component.first][val.first] );

      Histo.push_back(temp_histo);
      HistoCut.push_back(temp_histocut);

      Histo[Histo.size()-1]->SetMarkerColor(30+counter);
      HistoCut[HistoCut.size()-1]->SetMarkerColor(30+counter);
      
      //IntegralMap[temp_histo->Integral()] = Histo[Histo.size()-1];
      //IntegralMap_cut[temp_histo->Integral()] = HistoCut[Histo.size()-1];

      IntegralMap.insert({temp_histo->Integral(),Histo[Histo.size()-1]});
      IntegralMap_cut.insert({temp_histocut->Integral(),HistoCut[HistoCut.size()-1]});
      counter++;
    }// for on contaminant map with access to the element
  }//for on mass element

  THStack* Hstack = new THStack("Hstack","Hstack");
  THStack* Hstack_cut= new THStack("Hstack_cut","Hstack_cut");
  

  outDef->cd();

  hposXY->Write();
  hposYZ->Write();
  
  counter=0;
  
  for( std::multimap<double_t,TH1D*>::iterator i = IntegralMap.begin(); i != IntegralMap.end(); i++ ){
    i->second->Write();
    Hstack->Add(i->second);
    counter++;
  }

  counter=0;
  
  for( std::multimap<double_t,TH1D*>::iterator i = IntegralMap_cut.begin(); i != IntegralMap_cut.end(); i++ ){
    i->second->Write();
    Hstack_cut->Add(i->second);
    counter++;
  }
  
  Hstack->Write();
  Hstack_cut->Write();
  
  outDef->Save();
  outDef->Close();
  return 0;
} catch (const std::exception& e) { std::cerr << e.what() << "\n"; return 1; }


bool isWithin(const std::map<Int_t,TVector3>& aMap,const Double_t x,const Double_t y,const Double_t z,const Int_t Volnum){

  const Double_t VolumeSize_x=cygno::geometry::module.cathodeX;
  const Double_t VolumeSize_y=cygno::geometry::module.cathodeY;
  const Double_t VolumeSize_z=cygno::geometry::module.driftLength;

  Double_t FiducialCut_xy = 20;
  Double_t FiducialCut_z = 20;

  Double_t dx = abs(x-aMap.at(Volnum).X() );
  Double_t dy = abs(y-aMap.at(Volnum).Y() );
  Double_t dz = abs(z-aMap.at(Volnum).Z() );

  bool cond = (dx <= (VolumeSize_x/2-FiducialCut_xy) && dy <= (VolumeSize_y/2-FiducialCut_xy) && dz <= (VolumeSize_z/2-FiducialCut_z) );

  //std::cout << "VolNum: " << Volnum << "  Center:  " << aMap.at(Volnum).X()<<"\t" << aMap.at(Volnum).Y()<<"\t" << aMap.at(Volnum).Z() << "  dist: " << dx<<"\t" << dy<<"\t" << dz << "\t" << cond << "\n";                               

  return cond;
}


TVector3* RelativePos(const std::map<Int_t,TVector3>& aMap,const Double_t x,const Double_t y,const Double_t z,const Int_t Volnum){

  Double_t dx = x-aMap.at(Volnum).X() ;
  Double_t dy = y-aMap.at(Volnum).Y() ;
  Double_t dz = z;

  TVector3* vec = new TVector3(dx,dy,dz);    
  //std::cout << "VolNum: " << Volnum << "  Center:  " << aMap.at(Volnum).X()<<"\t" << aMap.at(Volnum).Y()<<"\t" << aMap.at(Volnum).Z() << "  dist: " << dx<<"\t" << dy<<"\t" << dz << "\t" << cond << "\n";
  
  return vec;
}
