// ROOT post-processing: read step-level Hits, group selected charged-particle
// deposits by the existing event/nucleus/process logic and volume, write elabHits.
// Legacy branch bindings and grouping caveats are listed in docs/KNOWN_ISSUES.md.
#include <iostream>
#include "TFile.h"
#include "TTree.h"

int main(int argc, char** argv){

  std::string filename = argv[1];
  
  TFile* f = TFile::Open(filename.c_str());
  
  TTree* tree = (TTree*)f->Get("Hits");

  Int_t Evn,ParticleID,ParticleTag,ParentID,VolumeNumber;
  Double_t x_hits,y_hits,z_hits,VolumeTraslX,VolumeTraslY,VolumeTraslZ,EnergyDeposit;

  Char_t Nucleus[20];

  Char_t ParticleName[20];

  Char_t CreationProcess[20];
  
  tree->SetBranchAddress("EventNumber",&Evn);
  tree->SetBranchAddress("ParticleID",&ParticleID);
  tree->SetBranchAddress("ParticleTag",&ParticleTag);
  tree->SetBranchAddress("ParticleName",&ParticleName);
  tree->SetBranchAddress("ParentID",&ParentID);
  tree->SetBranchAddress("VolumeNumber",&VolumeNumber);
  tree->SetBranchAddress("x_hits",&x_hits);
  tree->SetBranchAddress("y_hits",&y_hits);
  tree->SetBranchAddress("z_hits",&z_hits);
  tree->SetBranchAddress("EnergyDeposit",&EnergyDeposit);
  tree->SetBranchAddress("VolumeNumber",&VolumeNumber);
  tree->SetBranchAddress("VolumeTraslX",&VolumeTraslX);
  tree->SetBranchAddress("VolumeTraslY",&VolumeTraslY);
  tree->SetBranchAddress("VolumeTraslZ",&VolumeTraslZ);
  tree->SetBranchAddress("Nucleus",&Nucleus);
  tree->SetBranchAddress("ProcessType",&CreationProcess);
  
  TFile* fout= new TFile(Form("elab_%s",filename.c_str()),"recreate");
  fout->cd();

  Int_t Out_evNumber;
  std::string Out_PartName;
  std::string Out_Nucl;
  Int_t Out_VolNum;
  Int_t Out_PartID;
  std::vector<Double_t> EDep_Out, VolNnum_Out, XVertex_Out, YVertex_Out, ZVertex_Out;

  std::map<Int_t, double_t> EVolumeMap;
  std::vector<Int_t> VolumNumList;
 
  std::string Out_Process;
  
  TTree* outTree = new TTree("elabHits","elabHits");
  outTree->Branch("evNumber",&Out_evNumber);
  outTree->Branch("PartName",&Out_PartName);
  outTree->Branch("EDep_Out",&EDep_Out);
  outTree->Branch("VolNnum_Out",&VolNnum_Out);
  outTree->Branch("Nucleus",&Out_Nucl);
  outTree->Branch("X_Vertex",&XVertex_Out);
  outTree->Branch("Y_Vertex",&YVertex_Out);
  outTree->Branch("Z_Vertex",&ZVertex_Out);
  
  Int_t flag=0;
  Int_t Nentries = tree->GetEntries();

  tree->GetEntry(0);
  Out_Nucl=Nucleus;
  Out_Process = CreationProcess;
  Out_evNumber = Evn;
  
  for(int i=0;i<Nentries;i++){
    tree->GetEntry(i);

    if(i%10000==0) std::cout << i <<"/" << Nentries << "\n";
    
    if(strcmp(ParticleName,"e-")!=0 && strcmp(ParticleName,"e+")!=0 && strcmp(ParticleName,"alpha")!=0){
  
      continue;

      //check the phot creation process
    }else if( strcmp(CreationProcess,Out_Process.c_str())==0  &&  strcmp(Nucleus,Out_Nucl.c_str())==0  &&  flag == 0 && Out_evNumber == Evn){

      Out_evNumber = Evn;
      Out_PartName = ParticleName;
      Out_Nucl=Nucleus;

      if(EVolumeMap.find(VolumeNumber) == EVolumeMap.end()){
	XVertex_Out.push_back(x_hits);
	YVertex_Out.push_back(y_hits);
	ZVertex_Out.push_back(z_hits);	
	EVolumeMap[VolumeNumber]= EnergyDeposit;
	VolumNumList.push_back(VolumeNumber);
      } else {
	EVolumeMap[VolumeNumber]+=EnergyDeposit;
      }
      
    }else if( ((strcmp(CreationProcess,"ionIoni")==0 || strcmp(CreationProcess,"eIoni")==0)) ){
      
      flag=1;
      
      if(EVolumeMap.find(VolumeNumber) == EVolumeMap.end()){
	XVertex_Out.push_back(x_hits);
	YVertex_Out.push_back(y_hits);
	ZVertex_Out.push_back(z_hits);
	EVolumeMap[VolumeNumber]= EnergyDeposit;
	VolumNumList.push_back(VolumeNumber); 
      } else {
	EVolumeMap[VolumeNumber]+=EnergyDeposit;
      }

    }else{

      for(auto& vnum: VolumNumList){
	VolNnum_Out.push_back(vnum);
	EDep_Out.push_back(EVolumeMap[vnum]);
      }
      
      outTree->Fill();

      
      flag=0;
      EVolumeMap.clear();
      EDep_Out.clear(); VolNnum_Out.clear(); XVertex_Out.clear(); YVertex_Out.clear(); ZVertex_Out.clear(); VolumNumList.clear();

      Out_evNumber = Evn;
      Out_PartName = ParticleName;
      Out_Nucl=Nucleus;
      Out_Process=CreationProcess;
	
      if(EVolumeMap.find(VolumeNumber) == EVolumeMap.end()){
	XVertex_Out.push_back(x_hits);
	YVertex_Out.push_back(y_hits);
	ZVertex_Out.push_back(z_hits);	
	EVolumeMap[VolumeNumber]= EnergyDeposit;
	VolumNumList.push_back(VolumeNumber); 
      } else {
	EVolumeMap[VolumeNumber]+=EnergyDeposit;
      }

    }
    
  }//chiudo for

  outTree->Write();
  fout->Save();
  fout->Close();

}
