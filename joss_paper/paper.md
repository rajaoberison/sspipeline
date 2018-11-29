---
title: 'SSPipeline: A pipeline for estimating and characterizing uncertainty in coastal storm surge levels'
tags:
  - Python
  - storm surge
  - flood hazard
  - sea level
  - climate impacts
authors:
  - name: John M. Letey
    affiliation: 1
    email: john.letey@colorado.edu
  - name: Mingxuan Zhang
    affiliation: 1
    email: mingxuan.zhang@colorado.edu
  - name: Tony E. Wong
    orcid: 0000-0002-7304-3883
    affiliation: 1
    email: twong@psu.edu
affiliations:
  - name: Department of Computer Science, University of Colorado, Boulder, CO, USA
    index: 1
date: 17 August 2018
bibliography: paper.bib
---

# Summary
Effective management of coastal risks demands projections of flood hazards that account for a wide variety of potential sources of uncertainty. Two typical approaches for estimating flood hazards include (1) direct physical process-based modeling of the storms themselves and (2) statistical modeling of the distributions and relevant characteristics of extreme sea level events. Recently, flexible and efficient mechanistically-motivated models for sea-level change have become widely used for characterizing uncertainty in projections of mean sea levels [@Oppenheimer2016]. In order to complement these models for mean sea levels, there is also a need for fast and flexible estimates of extreme sea levels, and corresponding uncertainties. This is the motivating factor in the focus within the SSPipeline (Storm Surge Pipeline) project, that characterizes uncertainty in estimates of extreme sea levels, using a statistical modeling approach. Specifically, the SSPipeline project ingests and processes raw sea-level data and fits a statistical distribution to the extreme sea levels, which in turn permits estimation of the probabilities associated with these extremes.

In the SSPipeline, we implemented an API that only requires a user to configure a text file, which includes arguments for the tide gauge data set, some statistical modeling settings, and output options. The program will run, from a single terminal command, resulting in a suite of model calibration and diagnostic routines. The output consists of a set of diagnostic plots, data sets of calibrated parameters, and storm surge return level estimates. The program is modular so that developers can extend the options for statistical modeling or alter the model calibration methods employed if they so choose.

To begin, the user must specify a raw tide gauge data set for hourly sea levels, formatted in the manner of the University of Hawaii Sea Level Center (UHSLC) data repository in CSV format [@Caldwell2015]. This choice is motivated by the fact that the UHSLC repository provides hundreds of widely used, freely available, and research-quality data sets, with global spatial coverage. The user must designate the file system location of this data set, as well as a number of data processing options to generate the processed data set that will serve as calibration data to which we fit a distribution. At present, a generalized extreme value (GEV) distribution fitting annual block maximum sea levels is the only option, as it is both commonly used in the literature and the limiting distribution for a sequence of block maxima [@Coles2001]. Future code enhancements will include adding options for other statistical models, for example, generalized Pareto or lognormal distributions. The GEV distribution is specified by three parameters: (1) a location parameter, which governs the center of the distribution ($\mu$); (2) a scale parameter, which governs the width of the distribution ($\sigma$); and (3) a shape parameter, which governs the weight of the upper tail ($\xi$). The SSPipeline estimates the three parameters, using a Markov chain Monte Carlo parameter calibration approach to sample from the posterior distribution of the model parameters given the processed tide gauge data set [@Higdon2004]. In this calibration approach, the goodness-of-fit of the GEV distribution defined by a candidate set of parameters is quantified by comparing the modeled probability of a given storm surge height against the observed probabilities from the tide gauge data. The user configuration file specifies a variety of settings for the calibration method, including the number of parallel Markov chains to use for estimation, the number of iterations to simulate, and thresholds for thinning (to handle autocorrelation among the samples) and convergence of the Markov chains to the posterior distribution of the model parameters, given the tide gauge data.

The output from the SSPipeline includes a data set of GEV posterior parameter samples, data tables of flood heights and associated probabilities, and a set of figures to assess model goodness-of-fit and the estimated flood probabilities. Figure 1 provides an example of this diagnostic figure set: (1A) a probability plot where each data point corresponds to an observed sea-level extreme in which the x-value gives the modeled probability of observing that sea level in a given year, and the y-value gives the empirical probability of observing that sea level in a given year; (1B) a quantile plot that shows the model-estimated sea levels (x-axis) associated with the observed sea levels (y-axis); (1C) a return levels plot that shows the storm surge heights ("return levels", y-axis) associated with given return periods (how frequently one expects to observe such a storm, x-axis); and (1D) the best-fit GEV distribution, superimposed on the processed tide gauge data.

![Diagnostic output plots using tide gauge data from Grand Isle, Louisiana, USA.](figure1.png)

The modular nature of the project codes allows the addition of new features and extensions of the base codes, including options to fit alternative statistical models and projecting future flood hazard by incorporating potential non-stationary processes into the model [@Wong2018]. By providing base code to the community, our aim is to (1) enable others to incorporate more modeling uncertainties into their own flood hazard estimates, (2) provide a foundation on which a user community might work together to develop extensions on the existing codes, and (3) provide a pipeline with standard output diagnostics to facilitate comparisons of the extensions and features that users may add over time. This, in turn, may lead to a more thorough understanding and careful accounting of the impacts of various uncertainties and processes that affect flood hazard estimates.

# Acknowledgements
We thank Klaus Keller for fruitful conversations and XXX for feedback on early
versions of the codes.

# References
