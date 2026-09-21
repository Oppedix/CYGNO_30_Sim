
def GEMsTh232Gen():

    ElementGems=["Th232","Ra228","Ac228","Th228","Ra224","Rn220","Po216","Pb212","Bi212","Po212","Tl208"]
    ZElementGems=[90,88,89,90,88,86,84,82,83,84,81]
    NElements=[232,228,228,228,224,220,216,212,212,212,208]
    RadEl="GEMs"
    
    for i in range(len(ElementGems)):
        with open(RadEl+"_"+ElementGems[i]+".mac", 'w') as f:
            f.write("/process/eLoss/StepFunction 0.01 0.1 mm"+"\n")
            f.write("/run/verbose 0"+"\n")
            f.write("/event/verbose 0"+"\n")
            f.write("/random/setSeeds 575223199 8381234975"+"\n")
            f.write("/output/OutFile "+RadEl+"_"+ElementGems[i]+"\n")
            f.write("#Elements: Cathodes GEMs Rings Vessel Lens Sensors"+"\n")
            f.write("/detector/RadElement "+RadEl+"\n")
            f.write("/isotope/AtomicNumber "+str(ZElementGems[i])+"\n")
            f.write("/isotope/MassNumber "+str(NElements[i])+"\n")
            f.write("/run/beamOn 100000"+"\n")



def GenScriptGemsTh232():
    ElementGems=["Th232","Ra228","Ac228","Th228","Ra224","Rn220","Po216","Pb212","Bi212","Po212","Tl208"]
    ZElementGems=[90,88,89,90,88,86,84,82,83,84,81]
    NElements=[232,228,228,228,224,220,216,212,212,212,208]
    RadEl="GEMs"

    #GEMs_Bi212_t0.root
    
    for i in range(len(ElementGems)):
        print("cd ../ && ./rdecay01 ../mymacros_single/Th232_chain/"+RadEl+"_"+ElementGems[i]+".mac && cd outfiles_V2 && ./SimpleProcessEvents "+RadEl+"_"+ElementGems[i]+"_t0.root && rm "+RadEl+"_"+ElementGems[i]+"_t0.root")

def map4cTh235():
    ElementGems=["Th232","Ra228","Ac228","Th228","Ra224","Rn220","Po216","Pb212","Bi212","Po212","Tl208"]
    
    for i in range(len(ElementGems)):
        print('{\"'+ElementGems[i]+"\",5.45e-3},", end=' ')
    print("")
        
    for i in range(len(ElementGems)):
        print('{\"'+ElementGems[i]+"\",1e5},", end=' ')
    print("")
        

#######################################################################################

#######################################################################################

def GEMsU235Gen():

    ElementGems=["U235","Th231","Pa231","Ac227","Th227","Ra223","Rn219","Po215","Pb211","Bi211","Tl207","Fr223","Po211"]
    ZElementGems=[92,90,91,89,90,88,86,84,82,83,81,87,84]
    NElements=[235,231,231,227,227,223,219,215,211,211,207,223,211]
    RadEl="GEMs"
    
    for i in range(len(ElementGems)):
        with open(RadEl+"_"+ElementGems[i]+".mac", 'w') as f:
            f.write("/process/eLoss/StepFunction 0.01 0.1 mm"+"\n")
            f.write("/run/verbose 0"+"\n")
            f.write("/event/verbose 0"+"\n")
            f.write("#/random/setSeeds 57523199 8381234975"+"\n")
            f.write("/output/OutFile "+RadEl+"_"+ElementGems[i]+"\n")
            f.write("#Elements: Cathodes GEMs Rings Vessel Lens Sensors"+"\n")
            f.write("/detector/RadElement "+RadEl+"\n")
            f.write("/isotope/AtomicNumber "+str(ZElementGems[i])+"\n")
            f.write("/isotope/MassNumber "+str(NElements[i])+"\n")
            f.write("/run/beamOn 100000"+"\n")


def GenScriptGemsU235():
    
    ElementGems=["U235","Th231","Pa231","Ac227","Th227","Ra223","Rn219","Po215","Pb211","Bi211","Tl207","Fr223","Po211"]
    ZElementGems=[92,90,91,89,90,88,86,84,82,83,81,87,84]
    NElements=[235,231,231,227,227,223,219,215,211,211,207,223,211]
    RadEl="GEMs"
    
    #GEMs_Bi212_t0.root
    
    for i in range(len(ElementGems)):
        print("cd ../ && ./rdecay01 ../mymacros_single/U238_chain/"+RadEl+"_"+ElementGems[i]+".mac && cd outfiles_V2 && ./SimpleProcessEvents "+RadEl+"_"+ElementGems[i]+"_t0.root && rm "+RadEl+"_"+ElementGems[i]+"_t0.root")


def map4cU235():
    
    ElementGems=["U235","Th231","Pa231","Ac227","Th227","Ra223","Rn219","Po215","Pb211","Bi211","Tl207","Fr223","Po211"]
    for i in range(len(ElementGems)):
        print('{\"'+ElementGems[i]+"\",5.45e-3},", end=' ')
    print("")
        
    for i in range(len(ElementGems)):
        print('{\"'+ElementGems[i]+"\",1e5},", end=' ')
    print("")

map4cU235()
