import numpy as np
import matplotlib.pyplot as plt
import json
import os.path as path
import subprocess
import time
import glob
import FlareGenerator as FG
from astropy.io import fits

def analysis(flare=True, sinusoid=True, impulse=True, changepoint=True, noise=True, plot=True, posterior=0, filename=''):

    if isinstance(posterior, int):
        if posterior==0:
            print("Critical failure. No posterior argument passed to posterior_analyis.")
            return(1)

    # Creating directories to save to #
    
    if not filename:
        print("Warning: Filename not specified, defaulting to numbers.")
    if not path.exists("./Flake Results/"):
        print("Flake Results directory nonexistant. Creating directory...")
        subprocess.call(["mkdir", "Flake Results"])
        time.sleep(1) #Give the directory time to be made if not found
        if not path.exists("./Flake Results/"):
            print("Critical Error. Failed to create directory.")
            exit(1)
        
    emptyfolder=False #So recursive FITS mode does not overwrite itself

    #Filename handling and ObsLen finder
    
    fitsfile=False
    txtfile=False
    
    if filename[len(filename)-4:len(filename)].lower()=='fits':
        fitsfile=True
        extlen=5      #extlen - File extension length
        fitsdirectory='./FITS Files/'+filename
        hdu_list=fits.open('.FITS Files/'+filename)
        lightcurve=hdu_list['LIGHTCURVE']
        ctime=lightcurve.data.field('TIME')
             #time is a function, ctime - curve time
        flux=lightcurve.data.field('SAP_FLUX')
        hdu_list.close()
        ObsLen=((ctime[len(ctime)-1]-ctime[0])*24)
        
    elif filename[len(filename)-3:len(filename)].lower()=='txt':
        txtfile=True
        extlen=4
        txtfilen=np.loadtxt(filename)
        ObsLen=(txtfilen[:, 0][len(txtfilen[:, 0])-1]*24)


    savepath="./Flake Results/"+filename[0:len(filename)-extlen]+"/" #Used to pass to first elif statement
    while not emptyfolder:
        if not filename:
            i=1
            while not emptyfolder:
                savepath="./Flake Results/"+str(i)+"/"
                if path.exists(savepath):
                    i=i+1
                else:
                    print("Saving results to", savepath)
                    subprocess.call(["mkdir", savepath])
                    time.sleep(1)
                    if not path.exists(savepath):
                        print("Critical Error. Failed to create directory.")
                        exit(1)
                    emptyfolder=True
        
        elif path.exists(savepath):
            i=1
            while not emptyfolder:
                pathname="./Flake Results/"+filename[0:len(filename)-extlen]+str(i)+"/"
                if path.exists(pathname):
                    i=i+1
                else:
                    savepath="./Flake Results/"+filename[0:len(filename)-extlen]+str(i)+"/"
                    print("Saving results to", savepath)
                    subprocess.call(["mkdir", savepath])
                    time.sleep(1)
                    if not path.exists(savepath):
                        print("Critical Error. Failed to create directory.")
                        exit(1)
                    emptyfolder=True
        else:
            savepath="./Flake Results/"+filename[0:len(filename)-extlen]+"/"
            print("Saving results to", savepath)
            subprocess.call(["mkdir", savepath])
            time.sleep(1)
            if not path.exists(savepath):
                print("Critical Error. Failed to create directory.")
                exit(1)
            emptyfolder=True

            
    lbd=np.ceil(len(posterior)/30) #Loading Bar Divisions (Used later) Higher the denominator, the longer the bar

    # Counting 0 padding 
 
    cp=0
    NumCPDist=[0]*len(posterior)
    for i in range(0, len(posterior)):
        NumCPDist[i]=posterior[i,3]
        if int(posterior[i, 3])>cp:
            cp=int(posterior[i, 3])

    mns=0
    NumSinDist=[0]*len(posterior)
    for i in range(0, len(posterior)):
        NumSinDist[i]=posterior[i, 9+(2*(cp-1))]
        if int(posterior[i, 9+(2*(cp-1))])>mns:
            mns=int(posterior[i, 9+(2*(cp-1))])

    mnf=0
    NumFlaresDist=[0]*len(posterior)
    for i in range(0, len(posterior)):
        NumFlaresDist[i]=posterior[i, 16+(2*(cp-1))+(3*(mns-1))]
        if int(posterior[i, 16+(2*(cp-1))+(3*(mns-1))])>mnf:
               mnf=int(posterior[i, 16+(2*(cp-1))+(3*(mns-1))])

    mni=0
    NumImpulseDist=[0]*len(posterior)
    for i in range(0, len(posterior)):
        NumImpulseDist[i]=posterior[i, 26+(2*(cp-1))+(3*(mns-1))+(4*(mnf-1))]
        if int(posterior[i, 26+(2*(cp-1))+(3*(mns-1))+(4*(mnf-1))])>mni:
            mni=int(posterior[i, 26+(2*(cp-1))+(3*(mns-1))+(4*(mnf-1))])

    #Need to know cp (Max Change points) and mnf (Max Number of Flares) ans mns (Max Number of Sinusoids) for 0 padding in posterior.txt

    flaredict={} #Dictionary is required to store posterior samples to plot "probability mist"
    
    if plot:
        plt.ion()
    
    #Flare Section

    if flare:
        
        weights=[1/len(NumFlaresDist)]*len(NumFlaresDist)
        if plot:
            plt.figure(1)
            plt.subplot2grid((2,2), (0,0))
            plt.hist(NumFlaresDist, bins=1, weights=weights)
            plt.ylabel('Probability')
            plt.xlabel('Num Flares')
            plt.title('Number of Flares Distribution')

        for j in range(1, mnf+1):
            
            plt.figure(2)
            
            #Amplitude
            FlareAmps=[0]*len(posterior)
            for i in range(0, len(posterior)):
                FlareAmps[i]=posterior[i, (22+(2*(cp-1))+(3*(mns-1))+(j-1))]   
            AmpHist=plt.hist(FlareAmps, weights=weights)

            #Start Time (t0)
            t0=[0]*len(posterior)
            for i in range(0, len(posterior)):
                t0[i]=posterior[i, (21+(2*(cp-1))+(3*(mns-1))+(j-1))]
            t0Hist=plt.hist(t0, weights=weights)

            #Rise Time
            FlareRise=[0]*len(posterior)
            for i in range(0, len(posterior)):
                FlareRise[i]=(posterior[i, (23+(2*(cp-1))+(3*(mns-1))+(2*(mnf-1))+(j-1))])
            RiseHist=plt.hist(FlareRise, weights=weights)

            #Decay Time
            FlareDecay=[0]*len(posterior)
            for i in range(0, len(posterior)):
                FlareDecay[i]=(posterior[i, (24+(2*(cp-1))+(3*(mns-1))+(3*(mnf-1))+(j-1))])
            DecayHist=plt.hist(FlareDecay, weights=weights)

            if j==1:
                flaredict["Flares"]=[{"FlareAmps": FlareAmps, "t0": t0, "FlareRise": FlareRise, "FlareDecay": FlareDecay}]
            elif j>1:
                flaredict["Flares"].append({"FlareAmps": FlareAmps, "t0": t0, "FlareRise": FlareRise, "FlareDecay": FlareDecay})

                
            AmpMPP=0     #MPP Most Probable Probability
            t0MPP=0
            RiseMPP=0
            DecayMPP=0
            AmpMP=0      #MP Most Probable Value
            t0MP=0
            RiseMP=0
            DecayMP=0
            for i in range(0, len(AmpHist[0])):
                if AmpHist[0][i]>AmpMPP:
                    AmpMP=(AmpHist[1][i]+AmpHist[1][i+1])/2
                    AmpMPP=AmpHist[0][i]
            for i in range(0, len(t0Hist[0])):
                if t0Hist[0][i]>t0MPP:
                    t0MP=(t0Hist[1][i]+t0Hist[1][i+1])/2
                    t0MPP=t0Hist[0][i]
            for i in range(0, len(RiseHist[0])):
                if RiseHist[0][i]>RiseMPP:
                    RiseMP=(RiseHist[1][i]+RiseHist[1][i+1])/2
                    RiseMPP=RiseHist[0][i]
            for i in range(0, len(DecayHist[0])):
                if DecayHist[0][i]>DecayMPP:
                    DecayMP=(DecayHist[1][i]+DecayHist[1][i+1])/2
                    DecayMPP=DecayHist[0][i]


            t0MP=t0MP*48
            DecayMP=DecayMP*48
            RiseMP=RiseMP*48

            parameters={"FlareParameters":[{"GSTD":RiseMP, "EDTC":DecayMP, "Amp":AmpMP, "t0":t0MP, "FlareType":"GRED"}], "GlobalParameters":{"Noise":0, "ObsLen":ObsLen, "Graph": 1}}
            jsonfilename=savepath+"Flare"+str(j)+".json"
            filen=open(jsonfilename, 'w')
            json.dump(parameters, filen)
            filen.close()
                
    #Impulse Section

    if impulse:
        weights=[1/len(NumImpulseDist)]*len(NumImpulseDist)

        for j in range(1, mni+1):

            impulsename='impulse'+str(j)
            #t0
            It0=[0]*len(posterior)
            for i in range(0, len(posterior)):
                It0[i]=(posterior[i, 29+(2*(cp-1))+(3*(mns-1))+(4*(mnf-1))+(j-1)])/2

            It0Hist=plt.hist(t0, weights=weights)

            #Amp
            ImpAmp=[0]*len(posterior)
            for i in range(0, len(posterior)):
                ImpAmp[i]=posterior[i, 29+(2*(cp-1))+(3*(mns-1))+(4*(mnf-1))+(mni-1)+(j-1)]
            AmpHist=plt.hist(ImpAmp, weights=weights)

            impulsedict[impulsename]=[It0, ImpAmp]
            
            AmpMPP=0   #As before
            It0MPP=0
            AmpMP=0
            It0MP=0

            if j==1:
                flaredict["Impulses"]=[{"It0": It0, "ImpAmp": ImpAmp}]
            elif j>1:
                flaredict["Impulses"].append({"It0": It0, "ImpAmp": ImpAmp})
            
            for i in range(0, len(AmpHist[0])):
                if AmpHist[0][i]>AmpMPP:
                    AmpMP=(AmpHist[1][i]+AmpHist[1][i+1])/2
                    AmpMPP=AmpHist[0][i]
            for i in range(0, len(It0Hist[0])):
                if It0Hist[0][i]>t0MPP:
                    It0MP=(It0Hist[1][i]+It0Hist[1][i+1])/2
                    It0MPP=It0Hist[0][i]

            It0MP=It0MP*48
            
            parameters={"FlareParameters":[{"Amp":AmpMP, "t0":It0MP, "FlareType":"Impulse"}], "GlobalParameters":{"Noise":0, "ObsLen":ObsLen, "Graph": 1}}
            jsonfilename=savepath+"Impulse"+str(j)+".json"
            filen=open(jsonfilename, 'w')
            json.dump(parameters, filen)
            filen.close()

    #Sinusoid Section

    if sinusoid:
        weights=[1/len(NumSinDist)]*len(NumSinDist)
        if plot:
            plt.close()
            plt.figure(1)
            plt.subplot2grid((2,2), (0,1))
            plt.hist(NumSinDist, bins=1, weights=weights)
            plt.ylabel('Probability')
            plt.xlabel('Num Sinusoids')
            plt.title('Number of Sinusoids Distribution')

        for j in range(1, mns+1):

            plt.figure(2)

            #Period
            SinP=[0]*len(posterior)
            for i in range(0, len(posterior)):
                SinP[i]=np.e**(posterior[i, 12+2*(cp-1)])
                #e** as this is the log(period)
            PHist=plt.hist(SinP, weights=weights)

            #Amp
            SinAmp=[0]*len(posterior)
            for i in range(0, len(posterior)):
                SinAmp[i]=posterior[i, 13+2*(cp-1)+(mns-1)]
            AmpHist=plt.hist(SinAmp, weights=weights)

            #Phase (In radians. How many bins is one radian?)
            SinPhase=[0]*len(posterior)
            for i in range(0, len(posterior)):
                SinPhase[i]=posterior[i, 14+2*(cp-1)+2*(mns-1)]
            PhaseHist=plt.hist(SinPhase, weights=weights)

            if j==1:
                flaredict["Sinusoids"]=[{"SinP": SinP, "SinAmp": SinAmp, "SinPhase": SinPhase}]
            elif j>0:
                flaredict["Sinusoids"].append({"SinP": SinP, "SinAmp": SinAmp, "SinPhase": SinPhase})
            
            AmpMPP=0        #As before
            PeriodMPP=0
            PhaseMPP=0
            AmpMP=0
            PeriodMP=0
            PhaseMP=0

            for i in range(0, len(AmpHist[0])):
                if AmpHist[0][i]>AmpMPP:
                    AmpMP=(AmpHist[1][i]+AmpHist[1][i+1])/2
                    AmpMPP=AmpHist[0][i]
            for i in range(0, len(PHist[0])):
                if PHist[0][i]>PeriodMPP:
                    PeriodMP=(PHist[1][i]+PHist[1][i+1])/2
                    PeriodMPP=PHist[0][i]
            for i in range(0, len(PhaseHist)):
                if PhaseHist[0][i]>PhaseMPP:
                    PhaseMP=(PhaseHist[1][i]+PhaseHist[1][i+1])/2
                    PhaseMPP=PhaseHist[0][i]

            parameters={"FlareParameters":[{"AmpMP":0, "t0":0, "FlareType":"N/A"}], "GlobalParameters":{"Noise":0, "ObsLen":ObsLen, "Graph": 1}, "Sinusoids":[{"Period":PeriodMP, "Phase":PhaseMP, "Amp":AmpMP}]}
            jsonfilename=savepath+"Sinusoid"+str(j)+".json"
            filen=open(jsonfilename, 'w')
            json.dump(parameters, filen)
            filen.close()
                
    #Change Points Section

    if changepoint:
        weights=[1/len(NumCPDist)]*len(NumCPDist)

        for j in range(1, cp+1):

            #t0
            cpt0=[0]*len(posterior)
            for i in range(0, len(posterior)):
                cpt0[i]=(posterior[i, 6+(j-1)])/2
            cpt0Hist=plt.hist(cpt0, weights=weights)

            #Amp
            Amp=[0]*len(posterior)
            for i in range(0, len(posterior)):
                Amp[i]=posterior[i, 6+cp+(j-1)]
            AmpHist=plt.hist(Amp, weights=weights)

            if j==1:
                flaredict["ChangePoints"]=[{"cpt0": cpt0, "Amp": Amp}]
            elif j>1:
                flaredict["ChangePoints"].append({"cpt0": cpt0, "Amp": Amp})
            
            t0MPP=0     #As before
            AmpMPP=0
            t0MP=0
            AmpMP=0

            for i in range(0, len(cpt0Hist[0])):
                if cpt0Hist[0][i]>t0MPP:
                    t0MP=(cpt0Hist[1][i]+cpt0Hist[1][i+1])/2
                    t0MPP=cpt0Hist[0][i]
            for i in range(0, len(AmpHist[0])):
                if AmpHist[0][i]>AmpMPP:
                    AmpMP=(AmpHist[1][i]+AmpHist[1][i+1])/2
                    AmpMPP=AmpHist[0][i]

            parameters={"FlareParameters":[{"AmpMP":0, "t0":0, "FlareType":"N/A"}], "GlobalParameters":{"Noise":0, "ObsLen":ObsLen, "Graph": 1}, "ChangePoints":[{"t0":t0MP, "Amp":AmpMP}]}
            jsonfilename=savepath+"ChangePoint"+str(j)+".json"
            filen=open(jsonfilename, 'w')
            json.dump(parameters, filen)
            filen.close()
            
    #Noise Section
        
    if noise:
        weights=[1/len(posterior)]*len(posterior)
        Noise=[0]*len(posterior)
        for i in range(0, len(posterior)):
            Noise[i]=posterior[i, 0]
        NoiseHist=plt.hist(Noise, weights=weights)

        nstdMP=0     #As before
        nstdMPP=0

        for i in range(0, len(NoiseHist[0])):
            if NoiseHist[0][i]>nstdMPP:
                nstdMP=(NoiseHist[1][i]+NoiseHist[1][i+1])/2
                nstdMPP=NoiseHist[0][i]

        parameters={"FlareParameters":[{"AmpMP":0, "t0":0, "FlareType":"N/A"}], "GlobalParameters":{"Noise":nstdMP, "ObsLen":ObsLen, "Graph": 1}}
        jsonfilename=savepath+"Noise.json"
        filen=open(jsonfilename, 'w')
        json.dump(parameters, filen)
        filen.close()


    #Probability Mist and Dictionary Reading
    
    if plot:
        plt.close()
        plt.figure(1)
        plt.subplot2grid((2,2), (1,0), colspan=2)
        
        print("Working...")

        for i in range(0, len(posterior)): #Iterating over the posterior samples
            #i is the posterior sample index and j is the object number index

            if noise:
                probmist={"GlobalParameters":{"Noise":Noise[i], "ObsLen": ObsLen, "Graph": 0}}

            elif not noise:
                probmist={"GlobalParameters":{"Noise":0, "ObsLen": ObsLen, "Graph": 0}}
                
            if flare:
                for j in range(0, mnf):
                    if j==0:
                        probmist["FlareParameters"]=[{"GSTD":flaredict["Flares"][j]["FlareRise"][i]*48, "EDTC":flaredict["Flares"][j]["FlareDecay"][i]*48, "Amp":flaredict["Flares"][j]["FlareAmps"][i], "t0":flaredict["Flares"][j]["t0"][i]*48, "FlareType": "GRED"}]
                    if j>1:
                        probmist["FlareParameters"].append({"GSTD":flaredict["Flares"][j]["FlareRise"][i]*48, "EDTC":flaredict["Flares"][j]["FlareDecay"][i]*48, "Amp":flaredict["Flares"][j]["FlareAmps"][i], "t0":flaredict["Flares"][j]["t0"][i]*48, "FlareType": "GRED"})

            if sinusoid:
                for j in range(0, mns):
                    if j==0:
                        probmist["Sinusoids"]=[{"Period": flaredict["Sinusoids"][j]["SinP"][i]*24, "Phase": flaredict["Sinusoids"][j]["SinPhase"][i]*24, "Amp": flaredict["Sinusoids"][j]["SinAmp"][i]}]
                    elif j>1:
                        probmist["Sinusoids"].append({"Period": flaredict["Sinusoids"][j]["SinP"][i]*24, "Phase": flaredict["Sinusoids"][j]["SinPhase"][i]*24, "Amp": flaredict["Sinusoids"][j]["SinAmp"][i]})

            if impulse:
                for j in range(0, mni):
                    if not flare and j==0:
                        probmist["FlareParameters"]=[{"Amp": flaredict["Impulses"][j]["ImpAmp"][i], "t0": flaredict["Impulses"][j]["It0"][i]*48, "FlareType": "Impulse"}]
                    elif flare or j>1:
                        probmist["FlareParameters"].append({"Amp": flaredict["Impulses"][j]["ImpAmp"][i], "t0": flaredict["Impulses"][j]["It0"][i]*48, "FlareType": "Impulse"})

            if changepoint:
                for j in range(0, cp):
                    if j==0:
                        probmist["ChangePoints"]=[{"t0": flaredict["ChangePoints"][j]["cpt0"][i]/2, "Amp": flaredict["ChangePoints"][j]["Amp"][i]}]
                    elif j>1:
                        probmist["ChangePoints"].append({"t0": flaredict["ChangePoints"][j]["cpt0"][i]/2, "Amp": flaredict["ChangePoints"][j]["Amp"][i]})

            filen=open('./probmist.json', 'w')
            json.dump(probmist, filen)
            filen.close()
            ptime, pflare=FG.FlareGenerator(pathh='./probmist.json')
            subprocess.call(["rm", "probmist.json"])
            if fitsfile:
                for k in range(0, len(ptime)):
                    ptime[k]=ptime[k]+ctime[0] #So time axes match
            plt.plot(ptime, pflare, alpha=1/len(posterior))

            for k in range(0, len(probmist["FlareParameters"])):
                probmist["FlareParameters"][k]["FlareType"]="N/A"  #Removing flares to plot only noise
                
            filen=open('./probmist.json', 'w')
            json.dump(probmist, filen)
            filen.close()
            ptime, pflare=FG.FlareGenerator(pathh='./probmist.json')
            subprocess.call(["rm", "probmist.json"])
            if fitsfile:
                for k in range(0, len(ptime)): 
                    ptime[k]=ptime[k]+ctime[0] #As before
            plt.plot(ptime, pflare, 'r', alpha=1/len(posterior))            

            #Nice loading bar
            print('\r[', end='')
            for l in range(0, int(np.ceil(i/lbd))):
                print('█', end='')
            for l in range(int(np.ceil(i/lbd)), int(np.floor((len(posterior))/lbd))):
                print('-', end='')
            print(']', end='')
            if i==len(posterior)-1:
                print('\nDone')
            
        if txtfile:
            plt.plot(np.loadtxt(filename)[:, 0], np.loadtxt(filename)[:, 1], 'y')
        elif fitsfile:
            for i in range(0, len(ctime)):
                ptime[i]=ptime[i]-ctime[0]
            plt.plot(ctime, flux, 'y')

        plt.title('Stellar Flare')
        plt.ylabel('Amplitude')
        plt.xlabel('Time (Days)')
        plt.suptitle('Flare Information')

    if plot:
        plt.ioff()
        plt.show()

    return(0)
