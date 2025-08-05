from mpl_toolkits.axes_grid1 import AxesGrid
from cartopy.mpl.geoaxes import GeoAxes
from matplotlib import pyplot as plt
import cartopy.feature as cfeature
import matplotlib.path as mpath
import cartopy.crs as ccrs


def conical_map(
    nrows_ncols,
    figsize_w=15.00,
    figsize_h=9.00,
    fontsize=10,
    axes_pad=(0.6, 0.40),
    title_pad=None,
    fig_layout=111,
    plot_titles=None,
    title_loc="center",
    cbar_on=False,
    shelf_zoom=False,
    ocean_color="#D1D7DB",
    cbar_location="bottom",
    cbar_per_sublot=False,
    cbar_pad=-0.1,
    cbar_size="2.75%",
    coast_lw=0.7,
    box_lw=1.70,
    dpi=96,
):
    """Template for base NWS map, Cartopy conical projection style."""

    # thicker border box
    plt.rcParams["axes.linewidth"] = box_lw
    # text font size
    plt.rcParams.update({"font.size": fontsize})

    # NearsidePerspective projection specification (NWS lat/lon constraints)
    proj = ccrs.NearsidePerspective(
        central_latitude=(40 + (64 - 40) / 2) + 2.5,
        central_longitude=(-20 + (13 - -20) / 2),
    )

    # axes class
    axes_class = (GeoAxes, dict(projection=proj))

    # figure
    fig = plt.figure(figsize=(figsize_w, figsize_h), dpi=dpi)

    # cbar specification
    if cbar_on:
        if cbar_per_sublot:
            cbar_mode = "each"
        else:
            cbar_mode = "single"
    else:
        cbar_mode = None

    # axes grid
    axgr = AxesGrid(
        fig,
        fig_layout,
        axes_class=axes_class,
        nrows_ncols=nrows_ncols,
        axes_pad=axes_pad,
        cbar_location=cbar_location,
        cbar_mode=cbar_mode,
        cbar_pad=cbar_pad,
        cbar_size=cbar_size,
        label_mode="keep",
    )

    # lat/lon boundaries (depending whether shelf zoom is turned on of off)
    if shelf_zoom:
        # lat/lon boundaries for zoomed in view of the shelf area
        latlim = [47, 63]
        lonlim = [-14.4, 10]
    else:
        # lat/lon boundaries trimming the nan buffer zone around the region
        latlim = [40.73337, 64.33455]
        lonlim = [-18.77779, 9.9997]

    # bordering, spacing etc.
    lower_space = 1.4  # can be altered if problems with arching at bottom if changing lat/lon limits
    rect = mpath.Path(
        [
            [lonlim[0], latlim[0]],
            [lonlim[1], latlim[0]],
            [lonlim[1], latlim[1]],
            [lonlim[0], latlim[1]],
            [lonlim[0], latlim[0]],
        ]
    ).interpolated(20)

    # template per subplot
    for i, ax in enumerate(axgr):
        # projection, transformations, extents etc.
        proj_to_data = ccrs.PlateCarree()._as_mpl_transform(ax) - ax.transData
        rect_in_target = proj_to_data.transform_path(rect)
        ax.set_boundary(rect_in_target)
        ax.set_extent([lonlim[0], lonlim[1], latlim[0] - lower_space, latlim[1]])

        # add map features
        ax.coastlines(color="black", linewidth=coast_lw, zorder=5)
        ax.add_feature(
            cfeature.LAND, color="tan", edgecolor="black", zorder=1, linewidth=0
        )
        ax.add_feature(cfeature.OCEAN, color=ocean_color)

        # add plot titles
        if plot_titles is not None:
            ax.set_title(
                plot_titles[i],
                pad=title_pad,
                loc=title_loc,
                fontweight=30,
                fontsize=fontsize,
            )

        # proj term to be used for plotting (useful for plotting purposes)
        plot_proj = ccrs.PlateCarree()

    return fig, axgr, plot_proj


def add_cbar(
    axgr,
    cbar_mappable,
    cbar_label=None,
    extend="neither",
    cbar_ticks=None,
    cbar_ticklabels=None,
):
    """
    Colorbar configuration add-on function to ConicalMap()
    If specified in ConicalMap() that a colorbar is needed, this accompanying function builds the colorbar for the grid of subplots.
    """

    # proceed by indexing through mappable objects if a list of mappables (for flexible indexing depending on whether one colorbar or colorbar for each)
    if isinstance(cbar_mappable, list):
        for i, ax in enumerate(axgr):
            # only proceed if the mappable instance is not None
            if cbar_mappable[i] is not None:
                cb = axgr.cbar_axes[i].colorbar(cbar_mappable[i], extend=extend)
                cax = axgr.cbar_axes[i]
                axis = cax.axis[cax.orientation]

                # if adding a colorbar label
                if cbar_label is not None:
                    # if list of different labels are provided
                    if isinstance(cbar_label, list):
                        axis.label.set_text(cbar_label[i])
                    # otherwise use same label provided for all cbars
                    else:
                        axis.label.set_text(cbar_label)

                # add custom ticks if turned on
                if cbar_ticks is not None:
                    cb.set_ticks(cbar_ticks[i])
                    # and add custom tick labels if turned on
                    if cbar_ticklabels is not None:
                        cb.set_ticklabels(cbar_ticklabels[i])

            # otherwise add no colorbar to this instance in the list
            elif cbar_mappable[i] == None:
                cb = axgr.cbar_axes[i].colorbar(cbar_mappable[i])
                cax = axgr.cbar_axes[i]
                axis = cax.axis[cax.orientation]
                # remove colorbar
                cb.remove()

    # otherwise produce colorbar for a single colorbar mappable
    else:
        cb = axgr.cbar_axes[0].colorbar(cbar_mappable, extend=extend)
        cax = axgr.cbar_axes[0]
        axis = cax.axis[cax.orientation]

        # if adding a colorbar label
        if cbar_label is not None:
            axis.label.set_text(cbar_label)

        # add custom ticks if turned on
        if isinstance(cbar_ticks, list):
            cb.set_ticks(cbar_ticks)
            # and add custom tick labels if turned on
            if cbar_ticklabels is not None:
                cb.set_ticklabels(cbar_ticklabels)
