
1;95;0c
void ProcessFile(std::string filename){

  TFile* f = TFile::Open(filename.c_str());
  
  TTree* tree = (TTree*)f->Get("Hits");

  Int_t Evn,ParticleID,ParticleTag,ParentID,VolumeNumber;
  Double_t x_hits,y_hits,z_hits,VolumeTraslX,VolumeTraslY,VolumeTraslZ,EnergyDeposit;

  Char_t Nucleus[10];

  Char_t ParticleName[10];

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
  tree->SetBranchAddress("ProcessType",&CreationProcess)
  
  TFile* fout= new TFile("test.root","recreate");

  fout->cd();
  
  Int_t Out_evNumber=0;
  std::string Out_PartName;
  double_t Out_TotalEdep=0;
  Int_t Out_VolNum;
  Int_t Out_PartID;
  Int_t Out_PartentID;

  std::string Temp_PartName;
  
  TTree* outTree = new TTree("elabHits","elabHits");

  outTree->Branch("evNumber",&Out_evNumber);
  outTree->Branch("PartName",&Out_PartName);
  outTree->Branch("Edep",&Out_TotalEdep);
  outTree->Branch("PartID",&Out_PartID);
  outTree->Branch("ParentID",&Out_ParentID);
  outTree->Branch("VolNum",&Out_VolNum);
    
  tree->GetEntry(0);
  
  Out_evNumber=Evn;
  Temp_PartName=ParticleName;
  Out_VolNum=VolumeNumber;
  
  for(int i=0;i<4000;i++){
    tree->GetEntry(i);

    //if neutrino CONTINUE

    //work with some flag on radioactive decay or not
    
    if(strcmp(ParticleName,"e-")!=0 && strcmp(ParticleName,"e+")!=0 && strcmp(ParticleName,"alpha")!=0){

      continue;
      
    }else if(Evn == Out_evNumber && Temp_PartName==ParticleName && Out_VolNum==VolumeNumber){

      if( strcmp(CreationProcess,"RadioactiveDecay")==0 ) Out_PartName=ParticleName;
      Out_TotalEdep+=EnergyDeposit;
      
    }else if( (strcmp(CreationProcess,"ionIoni")==0 || strcmp(CreationProcess,"eIoni")==0) && Out_VolNum==VolumeNumber ){

      Out_TotalEdep+=EnergyDeposit;
      Temp_PartName=ParticleName;
      
    }else {
      
      outTree->Fill();
      
      Out_evNumber=Evn;
      Out_PartName=ParticleName;
      Out_VolNum=VolumeNumber;
      Out_TotalEdep=0;

    }
    
  }//chiudo for

  outTree->Write();
  fout->Save();
  fout->Close();

}
