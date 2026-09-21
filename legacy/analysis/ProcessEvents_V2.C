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
  tree->SetBranchAddress("ProcessType",&CreationProcess);
  
  TFile* fout= new TFile("test.root","recreate");
  fout->cd();

  Int_t Out_evNumber;
  std::string Out_PartName;
  Int_t Nhits;
  Int_t Out_VolNum;
  Int_t Out_PartID;
  std::vector<Double_t> X_Out,Y_Out,Z_Out,EDep_Out,VolNnum_Out;
  
  TTree* outTree = new TTree("elabHits","elabHits");
  outTree->Branch("evNumber",&Out_evNumber);
  outTree->Branch("PartName",&Out_PartName);
  outTree->Branch("Nhits",&Nhits);
  outTree->Branch("X_out",&X_Out);
  outTree->Branch("Y_out",&Y_Out);
  outTree->Branch("Z_out",&Z_Out);
  outTree->Branch("EDep_Out",&EDep_Out);
  outTree->Branch("VolNnum_Out",&VolNnum_Out);
  outTree->Branch("Nucleus",&Out_Nucl);

  Int_t flag=0;
  Nhits=0;
  
  for(int i=0;i<tree->GetEntries();i++){
    tree->GetEntry(i);

    if(strcmp(ParticleName,"e-")!=0 && strcmp(ParticleName,"e+")!=0 && strcmp(ParticleName,"alpha")!=0){
      
      continue;
      
    }else if( strcmp(CreationProcess,"RadioactiveDecay")==0 && flag == 0 ){

      Out_evNumber = Evn;
      Out_PartName = ParticleName;
      Out_Nucl=Nucleus;
      Nhits++;
      X_Out.push_back(x_hits);
      Y_Out.push_back(y_hits);
      Z_Out.push_back(z_hits);
      EDep_Out.push_back(EnergyDeposit);
      VolNnum_Out.push_back(VolumeNumber);
            
    }else if( (strcmp(CreationProcess,"ionIoni")==0 || strcmp(CreationProcess,"eIoni")==0) ){

      flag=1;
      
      Nhits++;
      X_Out.push_back(x_hits);
      Y_Out.push_back(y_hits);
      Z_Out.push_back(z_hits);
      EDep_Out.push_back(EnergyDeposit);
      VolNnum_Out.push_back(VolumeNumber);

    }else{
                        
      outTree->Fill();

      flag=0;
      X_Out.clear(); Y_Out.clear(); Z_Out.clear(); EDep_Out.clear(); VolNnum_Out.clear();
      
      Nhits=1;
      Out_evNumber = Evn;
      Out_PartName = ParticleName;
      X_Out.push_back(x_hits);
      Y_Out.push_back(y_hits);
      Z_Out.push_back(z_hits);
      EDep_Out.push_back(EnergyDeposit);
      VolNnum_Out.push_back(VolumeNumber);
    }
    
  }//chiudo for

  outTree->Write();
  fout->Save();
  fout->Close();

}
