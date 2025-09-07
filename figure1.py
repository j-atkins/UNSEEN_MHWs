import ast
import numpy as np
import xarray as xr
import cmocean.cm as cmo
from matplotlib import pyplot as plt
from datetime import datetime, timedelta
from matplotlib.colors import LinearSegmentedColormap

from config import FPaths
from methods.plotting import conical_map, add_cbar
from methods.utils import interp_grid

# script specific params
PARAMS = {
    "regions_remove": [
        "Skagerrak Kattegat",
        "Armorican Shelf",
        "Norwegian Trench",
        "NE Atlantic S",
        "NE Atlantic N",
    ],
    "mask_choice": 2,
}

# =============================================================================
# data
# =============================================================================

# 1) obs

# 2023
obs_jja2023 = xr.open_dataset(FPaths.obs_daily_sst_jja2023)["analysed_sst"]
obs_june2023 = obs_jja2023.sel(time=slice("2023-06-01", "2023-06-30"))

# 1993-2016 period monthly
obs_clim_period = xr.open_dataset(FPaths.obs_monthly_sst)["analysed_sst"].sel(
    time=slice("1993-01-01", "2016-12-31")
)

obs_clim_june = obs_clim_period.where(
    obs_clim_period.time.dt.month == 6, drop=True
)  # june only

obs_clim_jmean = obs_clim_june.mean("time")  # june climatology

# shelf mean JJA daily climatology and 90th percentile (1993-2016)
shelf_mean_jjaclim = xr.open_dataset(FPaths.shelf_mean_climstats)["daily_climatology"]
shelf_mean_jja90th = xr.open_dataset(FPaths.shelf_mean_climstats)["percentile_90th"]

# june 2023 anomaly
obs_anom = obs_june2023.mean("time") - obs_clim_jmean  # june 2023 anomaly

# 2) masks, bathymetry etc.

mask_ds = xr.open_dataset(FPaths.shelfmask)
regions_mask = mask_ds.mask[PARAMS["mask_choice"], :, :]
regions_names_orig = ast.literal_eval(
    mask_ds.attrs["region_name_0" + str(PARAMS["mask_choice"])][18:]
)

regions_mask = regions_mask.rename({"y": "latitude", "x": "longitude"})

regions_mask["latitude"], regions_mask["longitude"] = (
    mask_ds["lat"].data,
    mask_ds["lon"].data,
)

shelf_mask = xr.DataArray(
    mask_ds.mask[1, :, :], [mask_ds.lat, mask_ds.lon], ["latitude", "longitude"]
)

bathy = xr.open_dataset(FPaths.bathymetry)["Bathymetry"]

# =============================================================================
# pre-processing
# =============================================================================

regions_names_processed = list(xr.open_dataset(FPaths.obs_sst_regmeans)["region"].data)

# remove unwanted regions
reg_idxs_mod_processed = [
    reg_idx
    for reg_idx in range(len(regions_names_processed))
    if regions_names_processed[reg_idx] not in PARAMS["regions_remove"]
]

regions_names_mod_processed = [
    regions_names_processed[i] for i in reg_idxs_mod_processed
]

# mask out unwanted regions
keep_indices = [regions_names_orig.index(r) for r in regions_names_mod_processed]
mask = np.isin(regions_mask, keep_indices)
regions_mask_plot = regions_mask.where(mask, np.nan)

# remap regions_mask_plot to consecutive integers starting from 0
unique_indices = np.sort(np.unique(regions_mask_plot))
remapped = np.full_like(regions_mask_plot, np.nan)
for new_idx, old_idx in enumerate(unique_indices):
    remapped[regions_mask_plot == old_idx] = new_idx

# interpolate shelf mask to obs
llon, llat = np.meshgrid(obs_clim_period["longitude"], obs_clim_period["latitude"])
lons, lats = (
    xr.DataArray(llon.ravel(), dims="target"),
    xr.DataArray(llat.ravel(), dims="target"),
)
mask_interp = interp_grid(shelf_mask, lats, lons, obs_clim_period)

# shelf mean obs for JJA 2023
shelf_mean_jja2023 = xr.DataArray(
    np.where(mask_interp == 1, obs_jja2023, np.nan),
    obs_jja2023.coords,
    obs_jja2023.dims,
).mean(("latitude", "longitude"))

# =============================================================================
# plot
# =============================================================================

# subplot titles
lettering = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
plot_titles = [
    r"$\bf{a}$" + ") NWS sub-regions",
    r"$\bf{b}$" + ") NWS June 2023",
    r"$\bf{c}$" + ") NWS JJA 2023 vs. climatology",
]

# subplots shape
subplot_grid = (1, 2)

# cmap
colors = [
    "#ef476f",
    "#f78c6b",
    "#ffd166",
    "#83d483",
    "#06d6a0",
    "#0cb0a9",
    "#118ab2",
    "#0A4F67",
]
custom = LinearSegmentedColormap.from_list("custom", colors[::-1])

# fig set up
fig, axgr, plot_proj = conical_map(
    nrows_ncols=subplot_grid,
    plot_titles=plot_titles,
    cbar_on=True,
    shelf_zoom=True,
    figsize_h=7,
    figsize_w=6.2,
    cbar_per_sublot=False,
    cbar_size="7.00%",
    axes_pad=(0.25, -0.1),
    cbar_pad=0.20,
    cbar_location="right",
    fontsize=10,
    dpi=300,
)

# UNSEEN hatching colour
plt.rcParams["hatch.color"] = "black"
plt.rcParams["hatch.linewidth"] = 0.55
plt.rcParams["font.size"] = 9.5

# per subplot/season
for i, ax in enumerate(axgr):
    ## 1) plot regions
    if i == 0:  # first subplot
        maps = ax.pcolormesh(
            regions_mask["longitude"].data,
            regions_mask["latitude"].data,
            remapped,
            transform=plot_proj,
            cmap=custom,
        )

        # add hatching in UNSEEN regions (hard coded)
        unseen_masked = np.where(
            ((remapped == 1) | (remapped == 7) | (remapped == 5)),
            True,
            np.nan,
        )  # central North Sea, Celtic Sea, Irish Shelf
        hatch = ax.contourf(
            regions_mask_plot["longitude"],
            regions_mask_plot["latitude"],
            unseen_masked,
            transform=plot_proj,
            colors="none",
            levels=[-1, 0, 1],
            hatches=[None, "//"],
        )

    ## 2) plot June 2023 anomaly map
    if i == 1:  # second subplot
        anom = ax.contourf(
            obs_anom["longitude"],
            obs_anom["latitude"],
            obs_anom,
            transform=plot_proj,
            cmap=cmo.balance,
            levels=np.arange(-3, 3 + 0.3, 0.3),
            extend="max",
        )

    # add contour of shelf break (with white outline)
    shelf = ax.contour(
        bathy["lon"],
        bathy["lat"],
        bathy,
        transform=plot_proj,
        zorder=5,
        levels=[200],
        colors=("black",),
        linestyles=("solid",),
        linewidths=(1.00,),
    )
    outline = ax.contour(
        bathy["lon"],
        bathy["lat"],
        bathy,
        transform=plot_proj,
        zorder=4,
        levels=[200],
        colors=("white",),
        linestyles=("solid",),
        linewidths=(2.00,),
    )

cbar_ticks = list(np.arange(-3, 3 + 1, 1))
add_cbar(
    axgr=axgr,
    cbar_mappable=anom,
    cbar_label="SST anomaly ($^\circ$C)",
    cbar_ticks=cbar_ticks,
)

## NWS-mean June 2023 timeseries plot as third subplot

ax3 = fig.add_axes([0.15, -0.02, 0.77, 0.28])

# jja day of year array
jja_doy = shelf_mean_jja2023["time"].dt.dayofyear

# convert to DDMM
ddmm = [
    (datetime(2023, 1, 1) + timedelta(days=int(doy) - 1)).strftime("%d/%m")
    for doy in jja_doy
]

# plot 2023
ax3.plot(
    jja_doy,
    shelf_mean_jja2023 - 273.15,
    lw=2.0,
    color="crimson",
    label="2023",
    zorder=5,
)

# climatology
ax3.plot(
    jja_doy,
    shelf_mean_jjaclim - 273.15,
    lw=1.5,
    color="black",
    ls="dashed",
    label="Mean (1993-2016)",
    zorder=4,
)

# 90th percentile
ax3.plot(
    jja_doy,
    shelf_mean_jja90th - 273.15,
    lw=1.75,
    color="black",
    ls="dotted",
    label="90th perc. (1993-2016)",
    zorder=4,
)

ax3.set_xticks(jja_doy[::15])
ax3.set_xticklabels(ddmm[::15])
ax3.set_xlabel("Date")
ax3.set_ylabel("SST ($^\circ$C)")
ax3.set_facecolor("gainsboro")
ax3.grid(color="white", linewidth=1)
ax3.set_title(plot_titles[-1], fontsize=10)

# shading for june
ax3.axvspan(
    jja_doy[0], jja_doy[30], alpha=0.75, color="darkgrey"
)  # days of year corresponding to june

ax3.legend(loc="lower right", fontsize=9)

plt.show()

# fig.savefig("plot_images/figure1.png", dpi=300, bbox_inches="tight")
