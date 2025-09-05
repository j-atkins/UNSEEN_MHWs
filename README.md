## Summary

Accompanying Python code for Atkins et al. (2025). Recent European marine heatwaves are unprecedented but not unexpected. *Communications Earth & Environment*. [Accepted].

Includes all code and data required to perform UNSEEN analysis and make all figures as they appear in the main text and supplement. 

## Contents

| File | Description |
| ----- | ----- |
| config.py | Master file for specifying UNSEEN analysis parameters and data file paths in configuration objects. |
| figure*.py | Manuscript and supplement figure code. |
| methods/ | Directory containing UNSEEN, plotting and utility functions for analysis. |
| LICENSE | Software licensing information. |
| README.md | This file. |
| environment.yml | YAML file for building Conda enironment. |
| data/ | Directory containing (zipped) processed data to produce figures. |

## Set up

This repository can be cloned to your local machine by:

`git clone https://github.com/j-atkins/UNSEEN_MHWs.git`

The [environment.yml](environment.yml) file can be used to create a Conda environment with all dependencies by:

`conda env create -f environment.yml`


```{note}
The contents of the `data/` directory (i.e. `compressed_data.zip`) must be unzipped and before they can be accessed by the analaysis and plotting scripts.
```

## Data

This section describes the source data used in this study. Processed forms of the data, ready for analysis and plotting (including sub-region means versions), are stored in the `data/` directory of this repo.

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
