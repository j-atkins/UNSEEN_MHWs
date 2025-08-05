import numpy as np
import xarray as xr
from matplotlib import pyplot as plt
import matplotlib.patheffects as pe

from config import FPaths, UNSEENConfig
import methods.unseen as un
from methods.utils import load_sst_dataset, extract_target_days

# script specific params
PARAMS = {
    "season_name": UNSEENConfig.season_names,
    "season_indices": UNSEENConfig.target_indices,
    "pivot_year": UNSEENConfig.pivot_year,
    "ft_pivot_years": xr.DataArray(
        np.arange(1993, 2024 + 1), [np.arange(1993, 2024 + 1)], ["year"]
    ),
    "n_iterations": 1000,
    "trend_source": "obs",
}

extrapolated = PARAMS["trend_source"] == "model"

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
obs_season_full["time"] = large_da["time"]
obs_season_match["time"] = large_da["time"]

# obs june 2023
june2023 = load_sst_dataset(
    FPaths.obs_sst_regmeans,
    UNSEENConfig.regions_choices,
    ("2023-06-01", "2023-06-30"),
)

# =============================================================================
# calculate june 2023 peak
# =============================================================================

june2023_anom = xr.DataArray(
    june2023.data
    - obs_season_match.where(obs_season_match.time.dt.month == 6, drop=True)
    .mean("year")
    .data,
    june2023.coords,
    june2023.dims,
)

june2023_resample = june2023_anom.rolling(
    time=UNSEENConfig.extr_avg_period, center=True
).mean("time")

june2023_peak = june2023_resample.max("time")

# =============================================================================
# pre-processing
# =============================================================================

# get unseen distribution
unseen_distr, _ = un.get_unseen_distr(
    large_da,
    UNSEENConfig.extr_avg_period,
    obs_season_full,
    trend_source=PARAMS["trend_source"],
    pivot_year=PARAMS["pivot_year"],
)

# get probabilities as function of strength of event
fs_risk = un.get_funcstrength_risk(
    unseen_distr,
    june2023_peak,
    degr_gthan=2.0,
    degr_step=0.1,
)

# get upper and lower 95% CI level for fs_risk
fs_perc_low, fs_perc_high = un.get_fs_perc_low_high(
    unseen_distr,
    june2023_peak,
    n_iterations=PARAMS["n_iterations"],
    degr_gthan=2.0,
    degr_step=0.1,
)

# get probabilities as function of time (/trend) [*** N.B. `_extrapolated` outputs are None when extrapolated == False]
ft_risk, ft_risk_extrapolated = un.get_functime_risk(
    model_da=large_da,
    trend_data=obs_season_full,
    extr_avg_period=UNSEENConfig.extr_avg_period,
    focus_event=june2023_peak,
    core_pivot_yrs=PARAMS["ft_pivot_years"],
    trend_source=PARAMS["trend_source"],
)

# get upper and lower 95% CI level for ft_risk [*** N.B. `_extrapolated` outputs are None when extrapolated == False]
ft_perc_low, ft_perc_high, ft_perc_low_extrapolated, ft_perc_high_extrapolated = (
    un.get_ft_perc_low_high(
        model_da=large_da,
        trend_data=obs_season_full,
        extr_avg_period=UNSEENConfig.extr_avg_period,
        focus_event=june2023_peak,
        n_iterations=PARAMS["n_iterations"],
        trend_source=PARAMS["trend_source"],
        core_pivot_yrs=PARAMS["ft_pivot_years"],
    )
)

# =============================================================================
# plot
# =============================================================================

plt.rcParams.update({"font.size": 10, "axes.linewidth": 1.0})

lettering = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
plot_titles = [rf"$\bf{{{let}}}$)" for let in lettering]

xlabels = [
    f"JJA-{UNSEENConfig.extr_avg_period}MAX ($^\circ$C)",
    "$^\circ$C > June 2023",
    "Year",
]
ylabels = ["Frequency", "Event chance", "Chance ≥ June 2023"]
xlims = [(-2, 6.0), (0, 2), (1992, 2025)]
ylims = [(0, 440), (0, 17), (0, 17)]
column_titles = ["Celtic Sea", "Central North Sea"]
colors = ["#DC647C", "#639FDA"]

nrows, ncols = 3, 2
fig, axs = plt.subplots(nrows, ncols, figsize=(7.2, 7.2), dpi=300)


def plot_unseen_distribution(ax, region_idx, region):
    color = colors[region_idx]
    data = unseen_distr.sel(region=region)
    ax.hist(
        data,
        bins=18,
        density=False,
        color=color,
        histtype="stepfilled",
        edgecolor="black",
        linewidth=1.3,
        alpha=1.0,
        label="UNSEEN (modelled)",
        zorder=5,
    )
    # june2023 2023 peak
    x = june2023_peak.sel(region=region).item()
    ax.axvline(
        x=x,
        color="black",
        linestyle="dashed",
        lw=2.25,
        label="June 2023 (observed)",
        zorder=6,
    )
    # percentile rank
    arr = np.sort(data.data)
    perc_rank = 100 * (1 - np.searchsorted(arr, x, side="right") / len(arr))
    ax.text(
        x + 0.2,
        265,
        f"{perc_rank:.1f}%",
        fontsize=10,
        zorder=6,
        color="black",
        rotation=90,
        fontweight="semibold",
    )
    ax.legend(loc="lower left", fontsize=8.3, ncols=1)


def plot_func_strength(ax, region_idx, region):
    color = colors[region_idx]
    ax.plot(
        fs_risk["increment"],
        fs_risk.sel(region=region),
        color=color,
        zorder=6,
        lw=2.0,
        path_effects=[pe.Stroke(linewidth=2.75, foreground="black"), pe.Normal()],
        solid_capstyle="butt",
    )
    ax.fill_between(
        fs_risk["increment"],
        fs_perc_low.sel(region=region),
        fs_perc_high.sel(region=region),
        color=color,
        alpha=0.4,
        zorder=5,
        edgecolor="black",
    )
    x_intervals = np.arange(0, 2.5, 0.5)
    y_intervals = np.arange(0, 20, 5)
    ax.set_xticks(x_intervals)
    ax.set_yticks(y_intervals)
    ax.set_xticklabels(x_intervals)
    ax.set_yticklabels([f"{y}%" for y in y_intervals])


def plot_func_time(ax, region_idx, region):
    color = colors[region_idx]

    # probabilities
    ax.plot(
        ft_risk["year"],
        ft_risk.sel(region=region),
        color=color,
        zorder=6,
        lw=2.0,
        path_effects=[pe.Stroke(linewidth=2.75, foreground="black"), pe.Normal()],
        solid_capstyle="butt",
    )

    if extrapolated:
        ax.plot(
            ft_risk_extrapolated["year"],
            ft_risk_extrapolated.sel(region=region),
            color=color,
            zorder=6,
            lw=2.0,
            path_effects=[
                pe.Stroke(linewidth=3.0, foreground="black"),
                pe.Normal(),
            ],
            solid_capstyle="butt",
        )

        # CI shading
        shading_low = xr.concat((ft_perc_low, ft_perc_low_extrapolated), dim="year")
        shading_high = xr.concat((ft_perc_high, ft_perc_high_extrapolated), dim="year")
        total_years = xr.concat(
            (large_da["year"], PARAMS["beyond_hindcast_yrs"]), dim="year"
        )
        ax.fill_between(
            total_years,
            shading_low.sel(region=region),
            shading_high.sel(region=region),
            color=color,
            alpha=0.4,
            zorder=5,
            edgecolor="black",
        )

    else:
        ax.fill_between(
            ft_risk["year"],
            ft_perc_low.sel(region=region),
            ft_perc_high.sel(region=region),
            color=color,
            alpha=0.4,
            zorder=5,
            edgecolor="black",
        )

    ax.axvline(
        x=2023, color="black", linestyle="dashed", lw=1.5, zorder=4, label="2023"
    )

    x_intervals = np.arange(1994, 2029, 6)
    y_intervals = np.arange(0, 20, 5)
    ax.set_xticks(x_intervals)
    ax.set_yticks(y_intervals)
    ax.set_xticklabels(x_intervals)
    ax.set_yticklabels([f"{y}%" for y in y_intervals])
    ax.legend(loc="upper left", fontsize=8.5, ncols=1)


# main plotting loop
for i, ax in enumerate(axs.flatten()):
    row, col = np.unravel_index(i, (nrows, ncols))
    region = unseen_distr["region"][col].item()

    if row == 0:
        plot_unseen_distribution(ax, col, region)
    elif row == 1:
        plot_func_strength(ax, col, region)
    elif row == 2:
        plot_func_time(ax, col, region)

    ax.set_facecolor("gainsboro")
    ax.grid(color="white", linewidth=1)
    ax.set_xlabel(xlabels[row], fontsize=10)
    if col == 0:
        ax.set_ylabel(ylabels[row], fontsize=10)
    else:
        ax.set_yticklabels([])
    ax.set_xlim(*xlims[row])
    ax.set_ylim(*ylims[row])
    ax.set_title(plot_titles[i], fontsize=10.5)

# column titles
for i, ax in enumerate(axs[0]):
    ax.text(
        0.5,
        1.275,
        column_titles[i],
        transform=ax.transAxes,
        ha="center",
        fontweight=530,
        fontsize=11.5,
    )

plt.tight_layout()
plt.savefig("plot_images/figure3.png", dpi=300, bbox_inches="tight")
