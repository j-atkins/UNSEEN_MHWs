import sys
import xarray as xr
import numpy as np
from calendar import monthrange


def load_sst_dataset(filepath, region, time_slice=None):
    ds = xr.open_dataset(filepath)["sst"]
    if time_slice:
        ds = ds.sel(time=slice(*time_slice))
    return ds.sel(region=region)


def print_progress(iteration, total, width=10):
    percent = int((float(iteration) / total) * 100.0)
    sys.stdout.write("\r{}%".format(percent))
    sys.stdout.flush()
    if iteration == total - 1:
        sys.stdout.write("\r" + " " * width + "\r")
        sys.stdout.flush()


def interp_grid(da, target_lats, target_lons, ref_file, method="nearest"):
    """Interpolate gridded data using dimensions of a reference file."""
    da_interp = da.interp(latitude=target_lats, longitude=target_lons, method=method)

    re_shape = (ref_file["latitude"].size, ref_file["longitude"].size)  # target shape

    unstack = xr.DataArray(
        data=da_interp.data.reshape(re_shape, order="C"),
        coords=[ref_file["latitude"], ref_file["longitude"]],
        dims=["latitude", "longitude"],
    )
    return unstack


def extract_target_days(var, years, season_indices, data_type="regmean"):
    """
    Generalised function for extracting individual days of a season. Now adapted for DJF data as well.
    N.B. does not work on ensemble datasets (i.e. across a `realisation` dimension).
    """

    month_digits = [
        "01",
        "02",
        "03",
        "04",
        "05",
        "06",
        "07",
        "08",
        "09",
        "10",
        "11",
        "12",
    ] * 2  # duplicated to allow for overspill

    # the years associated with the months of each season, e.g. 1993 DJF would be 1993,1994,1994 whereas JJA would be 1993,1993,1993
    syears = [
        [
            yr
            if m == 0 or (m != 0 and season_indices[m] > season_indices[0])
            else yr + 1
            for m in range(len(season_indices))
        ]
        for yr in years
    ]

    # number of days in the season, dependent on what year it is because leap years interact and use syears above to support seasons which span different years
    ndays = [
        sum(
            [
                monthrange(yr, month)[1]
                for yr, month in zip(syrs, np.array(season_indices) + 1)
            ]
        )
        for syrs in syears
    ]  # number of days in given season

    # time vectors [nd-1 here because + timedelta appears to be inclusive of the final value, i.e. extends into a day after the target period otherwise]
    ts = [
        [
            np.datetime64(f"{yr}-{month_digits[season_indices[0]]}-01"),
            np.datetime64(f"{yr}-{month_digits[season_indices[0]]}-01")
            + np.timedelta64(nd - 1, "D"),
        ]
        for nd, yr in zip(ndays, np.unique(var["time"].dt.year))
    ]

    # get daily data associated with target indices
    target_data = [var.sel(time=slice(t[0], t[1])) for t in ts]

    ## IF TARGET PERIOD CONTAINS A FEBRUARY
    ## where not a leap year (i.e. one less day in forecast period) fill final day with nan to match length of leap years

    # if Feb in season/target indices
    if 1 in season_indices:
        # create generic array to concatenate onto end of timeseries (singular time step, but maintaining the dim hence [])
        fill = np.full(target_data[0].isel(time=[0]).shape, np.nan)

        # concat empty (nan) array to time dim when not a leap year
        target_data_fill = [
            td.data
            if (
                (year + 1) % 4 == 0 and ((year + 1) % 100 != 0 or (year + 1) % 400 == 0)
            )
            else np.concatenate((td.data, fill), axis=1)
            for td, year in zip(target_data, years)
        ]

        # get time coord from any leap year to use as coord in full data
        ttime = target_data[
            list(years).index(2012 - 1)
        ][
            "time"
        ].data  # -1 year because predictions containing a leap year actually begin in Dec of previous year in this DJF set up

    # if no Feb
    else:
        # target_data and ttime as normal
        target_data_fill, ttime = (
            target_data,
            target_data[list(years).index(2010 - 1)]["time"].data,
        )

    # unstack using np methods
    if data_type == "map":
        target_data_fill = xr.DataArray(
            data=target_data_fill,
            coords=[years, ttime, var["latitude"], var["longitude"]],
            dims=["year", "time", "latitude", "longitude"],
        )
    else:
        target_data_fill = xr.DataArray(
            data=target_data_fill,
            coords=[years, var["region"], ttime],
            dims=["year", "region", "time"],
        ).transpose("region", "year", "time")

    return target_data_fill
