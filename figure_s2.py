import scipy
import numpy as np
import xarray as xr
from matplotlib import pyplot as plt

from config import FPaths, UNSEENConfig
from methods.utils import load_sst_dataset, extract_target_days, print_progress

# script specific params
PARAMS = {
    "season_indices": UNSEENConfig.target_indices,
    "n_iterations": 10000,
}

# =============================================================================
# data
# =============================================================================

# load model data
model_da = load_sst_dataset(
    FPaths.model_sst_regmeans,
    UNSEENConfig.regions_choices,
)

# combine all years (and all hindcasts, startdates, members) for large sample
large_da = model_da.stack(realisation=("hindcast", "startdate", "member")).sel(
    region=UNSEENConfig.regions_choices
)
large_da = large_da.drop_vars({"hindcast", "startdate", "member", "realisation"})
large_da["realisation"] = np.arange(large_da["realisation"].size)

# load obs
obs_full = load_sst_dataset(FPaths.obs_sst_regmeans, UNSEENConfig.regions_choices)

# ensure regions in model and obs match
if not np.array_equal(large_da["region"], obs_full["region"]):
    raise ValueError("Regions in model and obs must match.")

# extract seasonal data only from obs (in daily form)
obs_season_full = extract_target_days(
    obs_full, np.unique(obs_full.time.dt.year), PARAMS["season_indices"]
)

obs_season_full["time"] = large_da["time"]

# =============================================================================
# pre-processing
# =============================================================================


def bootstrap_pseudo_timeseries(
    dat,
    n_iterations,
):
    """Bootstrap model pseudo-timeseries. SST data across hindcast period."""

    pseudo_timeseries = []
    for r_idx, _ in enumerate(dat["region"]):
        print(f"Bootstrapping region: {r_idx + 1}/{len(dat.region)}")
        ts_tmp = []
        for ii in range(n_iterations):
            print_progress(ii, n_iterations)
            ts_tmp.append(
                [
                    np.random.choice(
                        dat.isel(region=r_idx).sel(year=yr), 1, replace=True
                    )[0]
                    for yr in dat["year"]
                ]
            )
        pseudo_timeseries.append(ts_tmp)

    pseudo_timeseries = xr.DataArray(
        data=pseudo_timeseries,
        coords=[
            dat["region"],
            np.arange(1, n_iterations + 1),
            dat["year"],
        ],
        dims=["region", "iteration", "year"],
    )

    return pseudo_timeseries


def calc_stats(xarr, dim="year"):
    return [
        xarr.mean(dim),
        xarr.std(dim),
        xarr.reduce(func=scipy.stats.skew, dim=dim),
        xarr.reduce(func=scipy.stats.kurtosis, dim=dim),
    ]


# bootstrapping
pseudo_timeseries = bootstrap_pseudo_timeseries(
    large_da.mean("time"),
    PARAMS["n_iterations"],
)


# model linear trend slope
model_sst_slopes = pseudo_timeseries.polyfit("year", deg=1)["polyfit_coefficients"].sel(
    degree=1
)

# obs linear trend slope (using full timeseries as this slope is what is used in main analysis)
obs_sst_slopes = (
    obs_season_full.mean("time")
    .polyfit("year", deg=1)["polyfit_coefficients"]
    .sel(degree=1)
)

# =============================================================================
# plot
# =============================================================================

lettering = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]
plot_titles = [r"$\bf{" + let + "}$" + ")" for let in lettering]

fig, axs = plt.subplots(1, 3, figsize=(7.2, 2), dpi=300)

# per subplot/season
for i, ax in enumerate(axs.flatten()):
    region = large_da["region"][i]
    model_dat = model_sst_slopes.sel(region=region)
    obs_dat = obs_sst_slopes.sel(region=region)

    if i == 0:
        color = "#DC647C"
    if i == 1:
        color = "#639FDA"
    if i == 2:
        color = "darkgrey"

    # model his
    distr_glosea = ax.hist(
        model_dat,
        bins=20,
        density=False,
        color=color,
        histtype="stepfilled",
        edgecolor="black",
        linewidth=1.2,
        alpha=1.0,
        label="GloSea",
        zorder=5,
    )

    # v line for obs mean
    ax.axvline(
        x=obs_dat,
        color="black",
        linestyle="dashed",
        lw=2.25,
        label="OSTIA",
        zorder=6,
    )

    # percentile rank of obs in model distribution
    arr, x = model_dat.data, obs_dat.data
    count_less_equal = count = sum(1 for a in arr if a <= x)
    perc_rank = (count_less_equal / len(arr)) * 100
    ax.text(x + 0.009, 500, str("%.2f" % float(perc_rank) + "%"), fontsize=10, zorder=6)

    #  formatting
    ax.set_xlabel("Trend ($^\circ$C yr$^{-1}$)", fontsize=10)
    ax.set_title(f"{plot_titles[i]} {UNSEENConfig.regions_choices[i]}", fontsize=10.5)
    ax.set_facecolor("gainsboro")
    ax.grid(color="white", linewidth=1, axis="x")
    ax.set_yticks([])  # blank


plt.tight_layout()
plt.savefig("plot_images/figure_s2.png", dpi=300, bbox_inches="tight")
