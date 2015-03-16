#include "FlareWave.h"
#include "RandomNumberGenerator.h"
#include "Utils.h"
#include "Data.h"
#include "CustomConfigFile.h"
#include <cmath>

using namespace std;
using namespace DNest3;

// FlareWaves contructor
FlareWave::FlareWave()
:waves(3,                                                   // number of parameters for each sinusoid (amplitude, phase and period)
       CustomConfigFile::get_instance().get_maxSinusoids(), // maximum number of sinusoids
       false,
       WaveDistribution(CustomConfigFile::get_instance().get_minLogPeriod(), // minimum log period for sinusoids
                        CustomConfigFile::get_instance().get_maxLogPeriod(), // maximum log period for sinusoids
                        CustomConfigFile::get_instance().get_minWaveMu(), // minumun of mu (mean of exponetial distribution for amplitudes)
                        CustomConfigFile::get_instance().get_maxWaveMu())), // maximum of mu
flares(4,
       CustomConfigFile::get_instance().get_maxFlares(),
       false,
       FlareDistribution(CustomConfigFile::get_instance().get_minFlareT0(), // minimum flare peak time scale
                         CustomConfigFile::get_instance().get_maxFlareT0(), // maximum flare peak time scale
                         CustomConfigFile::get_instance().get_minFlareMu(), // minimun of mu (mean of exponetial distribution for flare amplitudes)
                         CustomConfigFile::get_instance().get_maxFlareMu())),
mu(Data::get_instance().get_t().size())                    // initialise the model vector
{

}

void FlareWave::fromPrior()
{
  waves.fromPrior();
  waves.consolidate_diff();

  flares.fromPrior();
  flares.consolidate_diff();

  sigma = exp(log(1E-3) + log(1E6)*randomU());      // generate sigma from prior
  background = tan(M_PI*(0.97*randomU() - 0.485));  // generate background from Cauchy prior distribution
  background = exp(background);
}

double FlareWave::perturb()
{
  double logH = 0.;
  double randval = randomU();
  
  if(randval <= 0.2){ // perturb background sinusoids 20% of time
    logH += waves.perturb();
    waves.consolidate_diff();
  }
  else if(randval < 0.6){ // perturb flares 40% of time
    logH += flares.perturb();
    flares.consolidate_diff();
  }
  else if(randval < 0.8){ // perturb noise sigma 20% of time
    sigma = log(sigma);
    sigma += log(1E6)*randh();
    sigma = mod(sigma - log(1E-3), log(1E6)) + log(1E-3);
    sigma = exp(sigma);
  }
  else{ // perturb the background offset value 20% of time
    background = log(background);
    background = (atan(background)/M_PI + 0.485)/0.97;
    background += pow(10., 1.5 - 6.*randomU())*randn();
    background = mod(background, 1.);
    background = tan(M_PI*(0.97*background - 0.485));
    background = exp(background);
  }
  
  return logH;
}

double FlareWave::logLikelihood() const
{
  // Get the model components
  const vector< vector<double> >& componentsWave = waves.get_components();
  const vector< vector<double> >& componentsFlare = flares.get_components();

  // Get the data
  const vector<double>& t = Data::get_instance().get_t(); // times
  const vector<double>& y = Data::get_instance().get_y(); // light curve

  mu.assign(mu.size(), background); // assign all to the background level

  double logL = 0.;
  double invvar2 = 0.5/(sigma*sigma);
  double P, A, phi;
  double Af, trise, skew, t0, tscale;
  double dm;
  double lmv = -0.5*log(2.*M_PI*var);
  for(size_t j=0; j<(componentsWave.size()+componentsFlare.size()); j++){
    if ( j < componentsWave.size() ){
      P = exp(componentsWave[j][0]); // sinusoid period
      A = componentsWave[j][1];      // sinusoid amplitude
      phi = componentsWave[j][2];    // sinusoid initial phase
    
      for(size_t i=0; i<y.size(); i++){
        mu[i] += A*sin(2.*M_PI*(t[i]/P) + phi);
        dm = y[i]-mu[i];
        logL += lmv - dm*dm*invvar2;
      }
    }
    else{
      Af = componentsFlare[j-componentsWave.size()][1];    // flare amplitude
      t0 = componentsFlare[j-componentsWave.size()][0];    // flare t0
      trise = componentsFlare[j-componentsWave.size()][2]; // flare rise timescale
      skew = componentsFlare[j-componentsWave.size()][3];  // flare decay skew parameters

      for(size_t i=0; i<y.size(); i++){
        if ( t[i] < t0 ){ tscale = trise; }
        else { tscale = trise*skew; } // decay time is rise time times skew parameter

        mu[i] += Af*exp(-abs(t[i] - t0)/tscale);
        dm = y[i]-mu[i];
        logL += lmv - dm*dm*invvar2;
      }
    } 
  }

  return logL;
}

void FlareWave::print(std::ostream& out) const
{
  for(size_t i=0; i<mu.size(); i++)
    out<<mu[i]<<' ';
  out<<sigma<<' ';
  waves.print(out); out<<' ';
}

string FlareWave::description() const
{
  return string("objects, sigma");
}

