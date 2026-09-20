/*
Detector Number for the positive side of the Z axis
|2 5 8 11 14 17 20 23 26 ... 74|
|1 4 7 10 13 16 19 22 25 ... 73|
|0 3 6 9  12 15 18 21 24 ... 72|
Detector Number for the negative side of the Z axis
|75+2 ... 75+74|
|75+1 ... 75+73|
|75+0 ... 75+72|
*/




void BuildDetectorMap(std::map<Int_t,TVector3>& aMap){

  Double_t VolumeSize_x=500;
  Double_t VolumeSize_y=800;
  Double_t VolumeSize_z = 500;

  Double_t DetectorSpace=3;
  
  int counter=0;
  
  for(int i=-12;i<13;i++){
    for(int j=-1;j<2;j++){
      aMap[counter] = TVector3( i*(VolumeSize_x+DetectorSpace) , j*(VolumeSize_y+DetectorSpace) , VolumeSize_z/2  );
      counter++;
    }
  }
  
  
  for(int i=-12;i<13;i++){
    for(int j=-1;j<2;j++){
      aMap[counter] = TVector3( i*(VolumeSize_x+DetectorSpace) , j*(VolumeSize_y+DetectorSpace) , -VolumeSize_z/2  );
      counter++;
    }
  }

}





bool isWithin(const std::map<Int_t,TVector3>& aMap,const Double_t x,const Double_t y,const Double_t z,const Int_t Volnum){

  Double_t VolumeSize_x=500;
  Double_t VolumeSize_y=800;
  Double_t VolumeSize_z = 500;

  Double_t FiducialCut_xy = 20;
  Double_t FiducialCut_z = 20; 

  Double_t dx = abs(x-aMap.at(Volnum).X() );
  Double_t dy = abs(y-aMap.at(Volnum).Y() );
  Double_t dz = abs(z-aMap.at(Volnum).Z() );

  bool cond = (dx <= (VolumeSize_x/2-FiducialCut_xy) && dy <= (VolumeSize_y/2-FiducialCut_xy) && dz <= (VolumeSize_z/2-FiducialCut_z) );
    
  //std::cout << "VolNum: " << Volnum << "  Center:  " << aMap.at(Volnum).X()<<"\t" << aMap.at(Volnum).Y()<<"\t" << aMap.at(Volnum).Z() << "  dist: " << dx<<"\t" << dy<<"\t" << dz << "\t" << cond << "\n";
  
  return cond;
}




void PlotSpectra(std::string filename){

  std::map<Int_t,TVector3> VolCentroidMap;
  
  BuildDetectorMap(VolCentroidMap);
  
  TFile* f = TFile::Open(filename.c_str());
  
  TTree* tree = (TTree*)f->Get("elabHits");
  
  Int_t evNumber;
  std::string* PartName = nullptr;
  std::vector<double>* EDep=nullptr;
  std::vector<double>* VolNum=nullptr;
  std::string* Nucleus= nullptr;
  std::vector<double>* X_Vertex=nullptr;
  std::vector<double>* Y_Vertex=nullptr;
  std::vector<double>* Z_Vertex=nullptr;

  tree->SetBranchAddress("evNumber",&evNumber);
  tree->SetBranchAddress("PartName",&PartName);
  tree->SetBranchAddress("EDep_Out",&EDep);
  tree->SetBranchAddress("VolNnum_Out",&VolNum);
  tree->SetBranchAddress("Nucleus",&Nucleus);
  tree->SetBranchAddress("X_Vertex",&X_Vertex);
  tree->SetBranchAddress("Y_Vertex",&Y_Vertex);
  tree->SetBranchAddress("Z_Vertex",&Z_Vertex);

  TH1D* alphaplot = new TH1D("alphaplot","alphaplot",900,0,9000);
  TH1D* alphaplot_cut = new TH1D("alphaplot_cut","alphaplot_cut",900,0,9000);

  TH1D* betaplot = new TH1D("betaplot","betaplot",900,0,2000);
  TH1D* betaplot_cut = new TH1D("betaplot_cut","betaplot_cut",900,0,2000);

  /*
    
    for(auto [ndet,centr] : VolCentroidMap){
    std::cout << "detN " << ndet << "\t coord " << centr.X() << " " << centr.Y() << " " << centr.Z()<< "\n";
    }
    
  */
  
  for(int i =0; i<tree->GetEntries();i++){
    tree->GetEntry(i);

    if(i%10000 == 0) std::cout << i << "/" << tree->GetEntries()<< std::endl; 
    
    if(std::strcmp((*PartName).c_str(),"alpha")==0 ){
      for(int j=0; j<(*EDep).size();j++ ){

	if(isWithin( VolCentroidMap,(*X_Vertex)[j],(*Y_Vertex)[j],(*Z_Vertex)[j],(*VolNum)[j] )){
	  alphaplot_cut->Fill( (*EDep)[j]*1000 );
	}//chiudo if within the volume

	alphaplot->Fill( (*EDep)[j]*1000 ); 
	
      }//chiudo for on vector
    }//chiudo if on e-

    if(std::strcmp((*PartName).c_str(),"e+")==0 || std::strcmp((*PartName).c_str(),"e-")==0 ){
      for(int j=0; j<(*EDep).size();j++ ){

	if(isWithin( VolCentroidMap,(*X_Vertex)[j],(*Y_Vertex)[j],(*Z_Vertex)[j],(*VolNum)[j] )){
	  betaplot_cut->Fill( (*EDep)[j]*1000 );
	}//chiudo if within the volume

	betaplot->Fill( (*EDep)[j]*1000 ); 
	
      }//chiudo for on vector
    }//chiudo if on e-

    
    //std::cout << evNumber << "\t" << (*EDep)[0] <<"\t" << (*VolNum)[0] <<"\t"<< *PartName << std::endl;
    
  }//chiudo for

  alphaplot->Draw();
  new TCanvas();
  alphaplot_cut->Draw(); 
  new TCanvas();
  betaplot->Draw();
  new TCanvas();
  betaplot_cut->Draw();

  TFile* f_out = new TFile(Form("histo_%s",filename.c_str()),"recreate");
  f_out->cd();
  alphaplot->Write();
  alphaplot_cut->Write();
  betaplot->Write();
  betaplot_cut->Write();
  f_out->Save();
  f_out->Close();
  
}
