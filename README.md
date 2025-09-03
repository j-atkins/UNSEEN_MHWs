## Summary

Accompanying Python code for Atkins et al. (2025). Recent European marine heatwaves are unprecedented but not unexpected. *Communications Earth & Environment*. [Acccepted].

Includes code to perform UNSEEN analysis and make all figures as they appear in the main text and supplement. 

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

We also recommended making new `data` and `plot_images` directories (i.e. with `mkdir` on Linux/UNIX and OS X systems) to house the input data and store output figure .png files.

### 


## Data

This section describes the datasets (and formatting) required for the analysis code to work 'out of the box'. 

N.B. file paths are stored in the `FPaths` object in `config.py`. Users should update the paths to suit their own directory structures.

### Observations
OSTIA [near real-time](https://doi.org/10.48670/moi-00165) and [climate](https://doi.org/10.48670/moi-00168) data can be accessed from the Copernicus Marine Environment Monitoring Service. These two datasets should be concatenated to form `obs_daily_sst` which spans 1982-2024 (see below for further formatting details).

This data should be converted to NWS sub-regional mean data using a sub-regions mask to make `obs_sst_regmeans`. Please get in touch for details and access to the sub-regions mask used in the manuscript.

### Model
GloSea data can be accessed from [C3S](https://doi.org/10.24381/cds.181d637e) (this version is interpolated to a 1° × 1° grid).

Similarly to the observations, the model data should be converted to NWS sub-regional mean data using a sub-regions mask to make `model_sst_regmeans`. Please get in touch for details and access to the sub-regions mask used in the manuscript.

In this study, only GloSea data for the **JJA** forecast period are used (initalised on 25th April, 1st May and 9th May across each year of the hindcast period).

Dimensions and coordinates should be arranged as listed in the [model_sst_regmeans](#model_sst_regmeans) formatting section for the analysis code to work 'out of the box'.

### Formatting

A list (and formatting description) of each (**.nc**) file as used in the original manuscript is as follows:

1) #### `obs_daily_sst`

    ```python
    {
        "dimensions": {
            "latitude": "*size_of_latitude_dim*",
            "longitude": "*size_of_longitude_dim*",
            "time": "*size_of_time_dim*",
        },
        "coordinates": {
            "latitude": {
                "dims": ["latitude"],
                "data_type": "float32",
                "values_example": "[40.03, 40.08, ...]",
            },
            "longitude": {
                "dims": ["longitude"],
                "data_type": "float32",
                "values_example": "[-19.98, -19.92, ...]",
            },
            "time": {
                "dims": ["time"],
                "data_type": "datetime64[ns]",
                "values_example": "[1982-01-01, 1982-01-02, ...]",
            },
        },
        "data_variables": {
            "analyzed_sst": {
                "dims": ["latitude", "longitude", "time"],
                "data_type": "float64",
                "shape": "(*size_of_latitude_dim*, *size_of_longitude_dim*, *size_of_time_dim*)",
                "attributes": {
                    "long_name": "sea surface temperature",
                    "units": "°C",
                }
            },
        },
    }
    ```

2) #### `obs_sst_regmeans`

    ```python
    {
        "dimensions": {
            "region": "*size_of_region_dim*",
            "time": "*size_of_time_dim*",
        },
        "coordinates": {
            "region": {
                "dims": ["region"],
                "data_type": "str",
                "values_example": "['Celtic Sea', 'Central North Sea', ...]",
            },
            "time": {
                "dims": ["time"],
                "data_type": "datetime64[ns]",
                "values_example": "[1982-01-01, 1982-01-02, ...]",
            },
        },
        "data_variables": {
            "sst": {
                "dims": ["region", "time"],
                "data_type": "float32",
                "shape": "(*size_of_region_dim*, *size_of_time_dim*)",
                "attributes": {
                    "long_name": "Sea surface temperature",
                    "units": "°C",
                }
            },
        },
    }
    ```

3) #### `model_sst_regmeans`

    ```python
    {
        "dimensions": {
            "region": "*size_of_region_dim*",
            "hindcast": "*size_of_hindcast_dim*",
            "startdate": "*size_of_startdate_dim*",
            "year": "*size_of_year_dim*",
            "member": "*size_of_member_dim*",
            "time": "*size_of_time_dim*",
        },
        "coordinates": {
            "region": {
                "dims": ["region"],
                "data_type": "str",
                "values_example": "['Celtic Sea', 'Central North Sea', ...]",
            },
            "hindcast": {
                "dims": ["hindcast"],
                "data_type": "str",
                "values_example": "['glosea6_0', 'glosea6_1', ...]", # different runs of same system (e.g. GloSea6_1, GloSea5_2)
            },
            "startdate": {
                "dims": ["startdate"],
                "data_type": "str",
                "values_example": "['0425', '0501', '0509']", # 25th April, 1st May, 9th May
            },
            "year": {
                "dims": ["year"],
                "data_type": "int32",
                "values_example": "[1993, 1994, ..., 2016]", # hindcast year
            },
            "member": {
                "dims": ["member"],
                "data_type": "int32",
                "values_example": "[1, 2, ...]", # ensemble member
            },
                        
            "time": {
                "dims": ["time"],
                "data_type": "datetime64[ns]" | "str", # generic JJA days (year does not matter)
                "values_example": "[YYYY-06-01, YYYY-06-02, ..., YYYY-08-31]",
            },
        },
        "data_variables": {
            "sst": {
                "dims": ["region", "hindcast", "startdate", "year", "member", "time"],
                "data_type": "float32",
                "shape": "(*size_of_region_dim*, *size_of_hindcast_dim*, *size_of_startdate_dim*, *size_of_year_dim*, *size_of_member_dim*, *size_of_time_dim*)",
                "attributes": {
                    "long_name": "Sea surface temperature",
                    "units": "°C",
                }
            },
        },
    }
    ```

4) #### `bathymetry`

    ```python
    {
        "dimensions": {
            "lat": "*size_of_lat_dim*",
            "lon": "*size_of_lon_dim*",
        },
        "coordinates": {
            "lat": {
                "dims": ["lat"],
                "data_type": "float32",
                "values_example": "[40.07, 40.13, ...]",
            },
            "longitude": {
                "dims": ["longitude"],
                "data_type": "float32",
                "values_example": "[-19.89, -19.78, ...]",
            },
        },
        "data_variables": {
            "Bathymetry": {
                "dims": ["lat", "lon"],
                "data_type": "float32",
                "shape": "(*size_of_lat_dim*, *size_of_lon_dim*)",
                "attributes": {
                    "long_name": "bathymetry",
                    "units": "m",
                }
            },
        },
    }
    ```

5) #### shelfmask

    ```
    Please get in touch for details and access to the sub-regions mask used in the manuscript if you wish to use the same one.
    ```

## Contact

Jamie Atkins  
Institute for Marine and Atmospheric research Utrecht (IMAU)  
Utrecht University  
email: j.r.c.atkins@uu.nl
