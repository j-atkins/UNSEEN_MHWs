class UNSEENConfig:
    """Parameter choices for UNSEEN analysis"""

    extr_avg_period = 14  # [days], i.e. N in JJA-NMAX
    regions_choices = ["Celtic Sea", "Central North Sea", "Irish Shelf"]
    target_indices = (5, 6, 7)  # summer [J,J,A]
    season_names = "JJA"
    pivot_year = 2024  # for pivot detrending


class FPaths:
    """Input data (file) paths."""

    stem = "./"

    # full lat, lon fields (Fig. 1 only)
    obs_monthly_sst = (
        stem + "data/obs_SST_monthly_19932016.nc"
    )  # 1993-2016 period for climatology calc in Fig. 1 only
    obs_daily_sst_jja2023 = (
        stem + "data/obs_SST_daily_jja2023.nc"
    )  # Daily June 2023 isolated, Fig. 1 only

    # NWS-mean obs stats, i.e. daily climatology, 90th percentile (Fig. 1 only)
    shelf_mean_climstats = (
        stem + "data/NWS_clim_stats_19932016.nc"
    )  # calc across 1993-2016

    # sub-region means (data used in Figs. 2 and 3 + supplementary information)
    obs_sst_regmeans = (
        stem + "data/obs_SST_regmeans.nc"
    )  # daily; 1982-2024 (OSTIA clim and real-time concatenated)
    model_sst_regmeans = (
        stem + "data/model_SST_fullensemble_regmeans.nc"
    )  # daily; GloSea 1993-2016

    # misc.
    shelfmask = stem + "data/shelfmask.nc"
    bathymetry = stem + "data/bathymetry_NWS.nc"
