import numpy as np
from matplotlib import pyplot as plt
from scipy.stats import linregress


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

# load obs
obs = load_sst_dataset(FPaths.obs_sst_regmeans, UNSEENConfig.regions_choices)

obs_season = extract_target_days(
    obs, np.unique(obs.time.dt.year), PARAMS["season_indices"]
)

obs_means = obs_season.mean("time")  # seasonal means

# =============================================================================
# plots (obs)
# =============================================================================

# subplot grid shape
nrows, ncols = 3, 1

# set up
fig, axs = plt.subplots(nrows, ncols, figsize=(7.2, 7.5), dpi=300)

# ylims
yticks = [
    np.arange(14.5, 17 + 1, 1),
    np.arange(13.5, 16 + 1, 1),
    np.arange(12, 14.5 + 1, 1),
]

# ylocs for text
ylocs = [16.75, 15.65, 14.3]

# plot titles
lettering = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
plot_titles = [
    r"$\bf{" + let + "}$" + ") " + reg
    for let, reg in zip(lettering, UNSEENConfig.regions_choices)
]

# per subplot/season
for i, ax in enumerate(axs.flatten()):
    ax.scatter(
        obs_means["year"],
        obs_means.isel(region=i),
        color="white",
        edgecolor="black",
        s=30,
        marker="o",
        zorder=6,
        label="OSTIA",
    )

    # regression
    regr = linregress(obs_means["year"], obs_means.isel(region=i))
    ax.plot(
        obs_means["year"],
        regr.slope * obs_means["year"] + regr.intercept,
        lw=2.0,
        color="black",
        label="OSTIA linear fit",
    )

    # final point of obs fit
    ax.scatter(
        obs_means["year"][-1],
        (regr.slope * obs_means["year"] + regr.intercept)[-1],
        marker="X",
        color="crimson",
        edgecolor="black",
        s=100,
        zorder=6,
        label="Final fit value",
    )

    ax.set_xticks(np.arange(1982, 2024 + 6, 6))
    ax.set_yticks(yticks[i])

    # vertical fill for 1993-2016 period
    ax.axvspan(1993, 2016, alpha=0.75, color="darkgrey")

    # formatting
    ax.set_ylabel("JJA SST ($^\circ$C)")
    ax.set_facecolor("gainsboro")
    ax.grid(color="white", linewidth=1)
    ax.set_title(plot_titles[i], fontsize=10.5)

    if regr.pvalue < 0.01:
        p_text = "p < 0.01"
    elif regr.pvalue < 0.05:
        p_text = "p < 0.05"
    else:
        p_text = regr.pvalue

    ax.text(
        1981,
        ylocs[i],
        f"Slope = +{str(round(regr.slope, 3))} yr$^{{-1}}$\nr = {str(round(regr.rvalue, 2))}, {p_text}",
        fontsize=8.5,
        ha="left",
        va="bottom",
        bbox=dict(facecolor="white", edgecolor="black", boxstyle="round"),
        zorder=5,
    )

# legend
axs[-1].legend(loc="lower right", fontsize=8.5, ncols=3).set_zorder(7)

plt.tight_layout()
plt.savefig("plot_images/figure_s1.png", dpi=300, bbox_inches="tight")
