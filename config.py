class UNSEENConfig:
    """Parameter choices for UNSEEN analysis"""

    extr_avg_period = 14  # [days], i.e. N in JJA-NMAX
    regions_choices = ["Celtic Sea", "Central North Sea", "Irish Shelf"]
    target_indices = (5, 6, 7)  # summer [J,J,A]
    season_names = "JJA"
    pivot_year = 2024  # for pivot detrending


class FPaths:
    """Input and output (file) paths."""

    stem = "/path/to/repo/"

    obs_daily_sst = stem + "data/ostia_SST_daily.nc"
    obs_sst_regmeans = stem + "data/ostia_SST_regmeans.nc"
    model_sst_regmeans = stem + "data/model_SST_fullensemble_regmeans.nc"

    shelfmask = stem + "data/shelfmask.nc"
    bathymetry = stem + "data/bathymetry_NWS.nc"

