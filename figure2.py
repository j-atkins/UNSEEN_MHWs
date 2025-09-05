import scipy
import numpy as np
import xarray as xr
from matplotlib import pyplot as plt

import methods.unseen as un
from config import FPaths, UNSEENConfig
from methods.utils import load_sst_dataset, extract_target_days

# script specific params
PARAMS = {
    "season_name": UNSEENConfig.season_names,
    "season_indices": UNSEENConfig.target_indices,
    "pivot_year": UNSEENConfig.pivot_year,
    "n_iterations": 10000,
    "trend_source": "obs",
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
obs_match = load_sst_dataset(
    FPaths.obs_sst_regmeans,
    UNSEENConfig.regions_choices,
    ("1993-01-01", "2016-12-31"),
)

# ensure regions in model and obs match
if not np.array_equal(large_da["region"], obs_match["region"]):
    raise ValueError("Regions in model and obs must match.")

# extract seasonal data only from obs (in daily form)
obs_season_full = extract_target_days(
    obs_full, np.unique(obs_full.time.dt.year), PARAMS["season_indices"]
)
obs_season_match = extract_target_days(
    obs_match, np.unique(obs_match.time.dt.year), PARAMS["season_indices"]
)

obs_season_match["time"] = large_da["time"]


# =============================================================================
# pre-processing
# =============================================================================

# get model distribution
unseen_distr, diff_trends = un.get_unseen_distr(
    large_da,
    UNSEENConfig.extr_avg_period,
    obs_season_full,
    trend_source=PARAMS["trend_source"],
    pivot_year=PARAMS["pivot_year"],
)

# obs de-seasonalise and JJA-NMAX
obs_season_detrend = xr.DataArray(
    [
        obs_season_match.isel(region=r_idx) - diff_trends[r_idx]
        for r_idx in range(obs_season_match["region"].size)
    ],
    obs_season_match.coords,
    obs_season_match.dims,
)

obs_season_dseas = obs_season_detrend - obs_season_match.mean("year")

obs_max = (
    obs_season_dseas.rolling(time=UNSEENConfig.extr_avg_period, center=True)
    .mean("time")
    .max("time")
)


def bootstrap_pseudo_timeseries(
    unseen_distr,
    n_iterations,
    n_years,
):
    """Bootstrap mmodel pseudo-timeseries."""

    pseudo_timeseries = []
    for r_idx, region in enumerate(unseen_distr["region"]):
        print(f"Bootstrapping region: {r_idx + 1}/{len(unseen_distr.region)}")
        ts_tmp = [
            np.random.choice(unseen_distr.isel(region=r_idx), n_years, replace=True)
            for _ in range(n_iterations)
        ]
        pseudo_timeseries.append(ts_tmp)

    pseudo_timeseries = xr.DataArray(
        data=pseudo_timeseries,
        coords=[
            unseen_distr["region"],
            np.arange(1, n_iterations + 1),
            np.arange(1, n_years + 1),
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
    unseen_distr,
    PARAMS["n_iterations"],
    obs_max["year"].size,
)

# Calculate stats
model_plot_data = calc_stats(pseudo_timeseries, dim="year")
obs_plot_data = calc_stats(obs_max, dim="year")


# =============================================================================
# plots
# =============================================================================

# plot font size
plt.rcParams.update({"font.size": 10})

# plot border thickness
plt.rcParams["axes.linewidth"] = 1.0

# subplot titles
subplot_names = ["Mean", "Standard deviation", "Skewness", "Kurtosis"]
lettering = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]
plot_titles = [r"$\bf{" + let + "}$" + ")" for let in lettering]

# x axes labels
x_labels = [
    f"JJA-{UNSEENConfig.extr_avg_period}MAX ($^\circ$C)",
    f"JJA-{UNSEENConfig.extr_avg_period}MAX ($^\circ$C)",
    None,
    None,
]

# column and row titles
column_titles = UNSEENConfig.regions_choices
row_titles = [
    "Mean ($^\circ$C)",
    "Std. Deviation ($^\circ$C)",
    "Skewness",
    "Kurtosis",
]

# subplot grid shape
nrows, ncols = 4, len(UNSEENConfig.regions_choices)

# spacing for percentile annotation
spacings = [
    val
    for val in [0.04, 0.06, 0.1, 0.2]
    for _ in range(len(UNSEENConfig.regions_choices))
]  # duplicates each element, i.e. for each column


def plot_stat_histogram(
    ax, model_dat, obs_dat, color, spacing, title, region, stat_name
):
    """Plot histogram for a single statistic and region."""

    # model
    ax.hist(
        model_dat,
        bins=20,
        density=False,
        color=color,
        histtype="stepfilled",
        edgecolor="black",
        linewidth=1.2,
        alpha=1.0,
        label="Modelled",
        zorder=5,
    )

    # obs v line
    ax.axvline(
        x=obs_dat,
        color="black",
        linestyle="dashed",
        lw=2.25,
        label="Observed",
        zorder=6,
    )

    # percentile annotation
    arr, x = model_dat.data, obs_dat.data
    count_less_equal = sum(1 for a in arr if a <= x)
    perc_rank = (count_less_equal / len(arr)) * 100
    ax.text(
        obs_dat.data + spacing,
        490,
        f"{perc_rank:.2f}%",
        fontsize=10,
        zorder=6,
    )

    # format
    ax.set_title(title, fontsize=10.5)
    ax.set_facecolor("gainsboro")
    ax.grid(color="white", linewidth=1, axis="x")
    ax.set_yticks([])


fig, axs = plt.subplots(nrows, ncols, figsize=(7.2, 6.8), dpi=300)

region_colors = ["#DC647C", "#639FDA", "darkgrey"]

for i, ax in enumerate(axs.flatten()):
    idx_unravel = np.unravel_index(i, (nrows, ncols))
    region_idx = idx_unravel[1]
    stat_idx = idx_unravel[0]
    region = unseen_distr["region"][region_idx]
    model_dat = model_plot_data[stat_idx].sel(region=region)
    obs_dat = obs_plot_data[stat_idx].sel(region=region)
    color = region_colors[region_idx]
    plot_stat_histogram(
        ax,
        model_dat,
        obs_dat,
        color,
        spacings[i],
        plot_titles[i],
        region,
        subplot_names[stat_idx],
    )

# subplot column, row titles
vertical_titles_idxs = np.array([0 + (ncols * a) for a in range(nrows)])
horizontal_titles_idxs = np.arange(0, ncols)

for i, ax in enumerate(np.take(axs, horizontal_titles_idxs)):
    ax.text(
        0.50,
        1.40,
        column_titles[i],
        transform=ax.transAxes,
        ha="center",
        fontweight=530,
        fontsize=11.5,
    )

for i, ax in enumerate(np.take(axs, vertical_titles_idxs)):
    ax.text(
        -0.15,
        0.50,
        row_titles[i],
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontweight=530,
        fontsize=11.5,
        rotation=90,
    )

# legends
axs[0, 0].legend(loc="upper right", prop={"size": 9})
axs[0, 1].legend(loc="upper left", prop={"size": 9})
if len(UNSEENConfig.regions_choices) == 3:
    axs[0, 2].legend(loc="upper right", prop={"size": 9})

plt.tight_layout()

plt.show()

# plt.savefig("plot_images/figure2.png", dpi=300, bbox_inches="tight")
