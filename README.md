## Summary

Accompanying Python code for Atkins et al. (2025). Recent European marine heatwaves are unprecedented but not unexpected. *Communications Earth & Environment*.

Includes all code (plus guidance on data access) required to perform UNSEEN analysis and make all figures as they appear in the main text and supplement. 

## Contents

| File | Description |
| ----- | ----- |
| config.py | Master file for specifying UNSEEN analysis parameters and data file paths in configuration objects. |
| figure*.py | Manuscript and supplement figure code. |
| methods/ | Directory containing UNSEEN, plotting and utility functions for analysis. |
| LICENSE | Software licensing information. |
| README.md | This file. |
| environment.yml | YAML file for building Conda enironment. |

## Set up

This repository can be cloned to your local machine by:

`git clone https://github.com/j-atkins/UNSEEN_MHWs.git`

The [environment.yml](environment.yml) file can be used to create a Conda environment with all dependencies by:

`conda env create -f environment.yml`

**N.B.** The post-processed data from model/observational product output is housed in a separate Zenodo [repository](https://doi.org/10.5281/zenodo.17076446). To run the code 'out of the box', it is necessary to access the processed data from the Zenodo repository and house it in a new `data/` directory in this codebase repository.

## Data

This section describes the source data used in this study. Processed forms of the data, ready for analysis and plotting (including sub-region means versions), are housed in a separate Zenodo data repository, as described in the [Set up](#set-up).

### Observations
OSTIA [near real-time](https://doi.org/10.48670/moi-00165) and [climate](https://doi.org/10.48670/moi-00168) data can be accessed from the Copernicus Marine Environment Monitoring Service.

### Model
GloSea data can be accessed from [C3S](https://doi.org/10.24381/cds.181d637e) (this version is interpolated to a 1° × 1° grid).

In this study, only GloSea data for the **JJA** forecast period are used (initalised on 25th April, 1st May and 9th May across each year of the hindcast period).

## Contact

Jamie Atkins  
Institute for Marine and Atmospheric research Utrecht (IMAU)  
Utrecht University  
email: j.r.c.atkins@uu.nl
