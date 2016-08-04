//-----------------------------------------------------------------------
//
// Convoluted Landau and Gaussian Fitting Function
//         (using ROOT's Landau and Gauss functions)
//
//  Based on a Fortran code by R.Fruehwirth (fruhwirth@hephy.oeaw.ac.at)
//  Adapted for C++/ROOT by H.Pernegger (Heinz.Pernegger@cern.ch) and
//   Markus Friedl (Markus.Friedl@cern.ch)
//
//-----------------------------------------------------------------------

#include "TH1.h"
#include "TF1.h"
#include "TROOT.h"
#include "TStyle.h"
#include "TMath.h"

Double_t langaufun(Double_t *x, Double_t width, Double_t mpv, Double_t area, Double_t sigma) {

   //Fit parameters:
   //par[0]=Width (scale) parameter of Landau density
   //par[1]=Most Probable (MP, location) parameter of Landau density
   //par[2]=Total area (integral -inf to inf, normalization constant)
   //par[3]=Width (sigma) of convoluted Gaussian function
   //
   //In the Landau distribution (represented by the CERNLIB approximation),
   //the maximum is located at x=-0.22278298 with the location parameter=0.
   //This shift is corrected within this function, so that the actual
   //maximum is identical to the MP parameter.

      // Numeric constants
      Double_t invsq2pi = 0.3989422804014;   // (2 pi)^(-1/2)
      Double_t mpshift  = -0.22278298;       // Landau maximum location

      // Control constants
      Double_t np = 100.0;      // number of convolution steps
      Double_t sc =   5.0;      // convolution extends to +-sc Gaussian sigmas

      // Variables
      Double_t xx;
      Double_t mpc;
      Double_t fland;
      Double_t sum = 0.0;
      Double_t xlow,xupp;
      Double_t step;
      Double_t i;


      // MP shift correction
      mpc = mpv - mpshift * width;

      // Range of convolution integral
      xlow = x[0] - sc * sigma;
      xupp = x[0] + sc * sigma;

      step = (xupp-xlow) / np;

      // Convolution integral of Landau and Gaussian by sum
      for(i=1.0; i<=np/2; i++) {
         xx = xlow + (i-.5) * step;
         fland = TMath::Landau(xx,mpc,width) / width;
         sum += fland * TMath::Gaus(x[0],xx,sigma);

         xx = xupp - (i-.5) * step;
         fland = TMath::Landau(xx,mpc,width) / width;
         sum += fland * TMath::Gaus(x[0],xx,sigma);
      }

      return (area * step * sum * invsq2pi / sigma);
}
