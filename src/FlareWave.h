#ifndef _FlareWave_
#define _FlareWave_

#include <DNest4.h>
#include <vector>
#include <RJObject.h>
#include "WaveDistribution.h"
#include "FlareDistribution.h"
#include "ImpulseDistribution.h"
#include "ChangepointDistribution.h"

class FlareWave
{
  private:
    DNest4::RJObject<WaveDistribution> waves;              // sinusoid distribution
    DNest4::RJObject<FlareDistribution> flares;            // flare distribution
    DNest4::RJObject<ImpulseDistribution> impulse;         // impulse distribution
    DNest4::RJObject<ChangepointDistribution> changepoint; // background change point distribution
    
    double sigma; // Noise standard deviation
    double background; // A flat background offset level
    
  public:
    FlareWave(); // constructor

    // Generate the point from the prior
    void from_prior(DNest4::RNG& rng);

    // Metropolis-Hastings proposals
    double perturb(DNest4::RNG& rng);

    // Likelihood function (this also generates the model)
    double log_likelihood() const;
    
    // Print to stream
    void print(std::ostream& out) const;

    // Return string with column information
    std::string description() const;
};

#endif

