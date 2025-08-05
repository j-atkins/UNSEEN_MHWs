from scipy.stats import linregress
import xarray as xr
import numpy as np

from methods.utils import print_progress


def _calc_percentile(arr, x):
    """Calculate the exceedance probability (percentile rank) for value x in arr."""
    arr = np.asarray(arr)
    prob = 100 - (np.count_nonzero(arr <= x) / arr.size * 100)
    return prob


def _get_pivot_arr(
    seasonal_dat,
    year,
    region_idx,
    hindcast_years,
    system="obs",
    extrapolated=None,
    extrapolate_yrs=None,
):
    """
    Detrend timeseries by pivoting on a given year in a regression fit to the model ensemble data.
    Outputs an array (of len years in the model hindcast period) to subtract from the model data to get pivoted dataset.
    """
    if extrapolated and extrapolate_yrs is None:
        raise ValueError(
            "`extrapolate_yrs` array must be provided if extrapolated=True"
        )

    # regression
    if system == "obs":
        regr_gs = linregress(seasonal_dat["year"], seasonal_dat.isel(region=region_idx))
        y_pred = regr_gs.slope * seasonal_dat["year"] + regr_gs.intercept
    else:  # system == "model"
        regr_gs = linregress(
            seasonal_dat["year"],
            seasonal_dat.isel(region=region_idx).mean("realisation"),
        )
        if extrapolated:
            y_pred = regr_gs.slope * extrapolate_yrs + regr_gs.intercept
        else:
            y_pred = regr_gs.slope * seasonal_dat["year"] + regr_gs.intercept

    # y value for prescribed year
    y_point = float(y_pred.sel(year=year))

    # calc difference between trend line y point for presribed hindcast period

    if system == "obs":
        diff_trend = (regr_gs.slope * hindcast_years + regr_gs.intercept) - y_point
    else:  # system == "model"
        if extrapolated:
            diff_trend = (
                regr_gs.slope * seasonal_dat["year"] + regr_gs.intercept
            ) - y_point
        else:
            diff_trend = y_pred - y_point

    return diff_trend


def get_unseen_distr(
    model_da,
    extr_avg_period,
    trend_data,
    last_detrend=True,
    pivot_year=2024,
    trend_source="obs",
    extrapolated=None,
    extr_year=None,
):
    """Generate the UNSEEN ensemble DataArray for event distribution analysis."""
    if extrapolated and extr_year is None:
        raise ValueError("`extr_year` array must be provided if extrapolated=True")

    if last_detrend:
        diff_trends = []
        for r_idx in range(model_da["region"].size):
            pivot_args = {
                "seasonal_dat": trend_data.mean("time"),
                "year": pivot_year,
                "region_idx": r_idx,
                "hindcast_years": model_da["year"],
            }
            if trend_source == "model":
                pivot_args.update(
                    {
                        "system": "model",
                        "extrapolated": extrapolated,
                        "extrapolate_yrs": extr_year,
                    }
                )
            diff_trends.append(_get_pivot_arr(**pivot_args))
        model_da_detrend = model_da - xr.concat(diff_trends, dim="region")  # detrend
        model_da_dseas = model_da_detrend - model_da.mean("realisation").mean(
            "year"
        )  # anomaly/de-seasonalise
    else:
        model_da_dseas = model_da - model_da.mean("realisation").mean(
            "year"
        )  # anomaly/de-seasonalise

    # JJA-NMAX events
    large_max = (
        model_da_dseas.rolling(time=extr_avg_period, center=True)
        .mean("time")
        .max("time")
    )

    # stack and reset indices
    large_stacked = large_max.stack(sample=("realisation", "year"))
    large_stacked_reset = large_stacked.reset_index("sample")

    return large_stacked_reset, diff_trends


def get_funcstrength_risk(
    unseen_distr,
    focus_event,
    degr_gthan,
    degr_step,
):
    """Calculate probability of event occurrence at incremented strength relative to June 2023."""
    increments = np.arange(0, degr_gthan + degr_step, degr_step)
    risks_incremented = []
    for r_idx, region in enumerate(unseen_distr["region"]):
        arr = unseen_distr.isel(region=r_idx).data
        x_base = focus_event.sel(region=region).data
        risks_tmp = [_calc_percentile(arr, x_base + incre) for incre in increments]
        risks_incremented.append(risks_tmp)

    risks_incremented = xr.DataArray(
        risks_incremented,
        [unseen_distr["region"], increments],
        ["region", "increment"],
    )
    return risks_incremented


def get_fs_perc_low_high(
    unseen_distr,
    focus_event,
    n_iterations,
    degr_gthan,
    degr_step,
    quantile_low=0.025,
    quantile_high=0.975,
):
    """Calculate the 2.5th and 97.5th percentiles (95% CI, via bootstrapping) for the probability of events stronger than June 2023, from UNSEEN distributions."""
    increments = np.arange(0, degr_gthan + degr_step, degr_step)
    risks_bootstrapped = []
    print("Func-strength bootstrapping:")
    for r_idx, region in enumerate(unseen_distr["region"]):
        print(f"Region: {r_idx + 1}/{unseen_distr.region.size}")
        arr = unseen_distr.isel(region=r_idx).data
        x_base = focus_event.sel(region=region).data
        risks_incre = []
        for ii, incre in enumerate(increments):
            print_progress(ii, increments.size)
            risk_tmp = []
            for _ in range(n_iterations):
                random_idxs = np.random.randint(0, arr.size, size=arr.size)
                random_sample = arr[random_idxs]
                prob = _calc_percentile(random_sample, x_base + incre)
                risk_tmp.append(prob)
            risks_incre.append(risk_tmp)
        risks_bootstrapped.append(risks_incre)
    risks_bootstrapped = xr.DataArray(
        risks_bootstrapped,
        [
            unseen_distr["region"],
            increments,
            np.arange(n_iterations) + 1,
        ],
        ["region", "increment", "iteration"],
    )

    # calculate 2.5th and 97.5th percentiles for 95% confidence interval shading
    fs_perc_low = risks_bootstrapped.quantile(quantile_low, dim="iteration")
    fs_perc_high = risks_bootstrapped.quantile(quantile_high, dim="iteration")

    return fs_perc_low, fs_perc_high


def get_functime_risk(
    model_da,
    trend_data,
    extr_avg_period,
    focus_event,
    core_pivot_yrs,
    trend_source="obs",
    extrapolated=None,
    extrapolate_yrs=None,
):
    """
    Calculate the probability (percentile rank) of June 2023-like events as a function of time (pivot year),
    for both the hindcast period and (optionally) extrapolated years.
    """

    def calc_risks(pivot_years, trend_source, extrapolated=False, extrapolate_yrs=None):
        risks = []
        for r_idx, region in enumerate(model_da["region"]):
            # detrend for each pivot year
            diff_trends = [
                _get_pivot_arr(
                    seasonal_dat=trend_data.mean("time"),
                    year=yr,
                    region_idx=r_idx,
                    hindcast_years=model_da["year"],
                    system=trend_source,
                    extrapolated=extrapolated,
                    extrapolate_yrs=extrapolate_yrs,
                )
                for yr in pivot_years
            ]
            model_da_detrend = xr.DataArray(
                [model_da.isel(region=r_idx) - dtrend for dtrend in diff_trends],
                [pivot_years, model_da["year"], model_da.time, model_da.realisation],
                ["pivot", "year", "time", "realisation"],
            )

            # probability for each pivot year
            probs = []
            for md_pivot in model_da_detrend:
                model_da_dseas = md_pivot - model_da.isel(region=r_idx).mean(
                    "realisation"
                ).mean("year")
                model_max = (
                    model_da_dseas.rolling(time=extr_avg_period, center=True)
                    .mean("time")
                    .max("time")
                )
                model_stacked = model_max.stack(sample=("realisation", "year"))
                arr = model_stacked.data
                x = focus_event.sel(region=region).data
                prob = _calc_percentile(arr, x)
                probs.append(prob)
            risks.append(probs)

        return xr.DataArray(
            risks, [model_da["region"], pivot_years], ["region", "year"]
        )

    # core period
    risks = calc_risks(core_pivot_yrs, trend_source, extrapolated=False)

    # extrapolated period (optional)
    risks_extrapolated = None
    if extrapolated:
        if extrapolate_yrs is None:
            raise ValueError(
                "`extrapolate_yrs` array must be provided if extrapolated=True"
            )
        risks_extrapolated = calc_risks(
            extrapolate_yrs,
            "model",
            extrapolated=True,
            extrapolate_yrs=extrapolate_yrs,
        )

    return risks, risks_extrapolated


def get_ft_perc_low_high(
    model_da,
    trend_data,
    extr_avg_period,
    focus_event,
    n_iterations,
    core_pivot_yrs,
    trend_source="obs",
    extrapolated=None,
    extrapolate_yrs=None,
    quantile_low=0.025,
    quantile_high=0.975,
):
    """
    Calculate the 2.5th and 97.5th percentiles (95% CI, via bootstrapping) for the probability of June 2023-like events as function of time (pivot year),
    for both the hindcast period and (optionally) extrapolated years.
    """

    def calc_bootstrap_quantiles(
        pivot_years, trend_source, extrapolated=False, extrapolate_yrs=None
    ):
        risks_bootstrapped = []
        for r_idx, region in enumerate(model_da["region"]):
            print(f"Region: {r_idx + 1}/{model_da['region'].size}")
            # detrend for each pivot year
            diff_trends = [
                _get_pivot_arr(
                    seasonal_dat=trend_data.mean("time"),
                    year=yr,
                    region_idx=r_idx,
                    hindcast_years=model_da["year"],
                    system=trend_source,
                    extrapolated=extrapolated,
                    extrapolate_yrs=extrapolate_yrs,
                )
                for yr in pivot_years
            ]
            model_da_detrend = xr.DataArray(
                [model_da.isel(region=r_idx) - dtrend for dtrend in diff_trends],
                [pivot_years, model_da.year, model_da.time, model_da.realisation],
                ["pivot", "year", "time", "realisation"],
            )

            probs_years = []
            for p_idx, md_pivot in enumerate(model_da_detrend):
                print_progress(p_idx, model_da_detrend["pivot"].size)
                model_da_dseas = md_pivot - model_da.isel(region=r_idx).mean(
                    "realisation"
                ).mean("year")
                model_max = (
                    model_da_dseas.rolling(time=extr_avg_period, center=True)
                    .mean("time")
                    .max("time")
                )
                model_stacked = model_max.stack(sample=("realisation", "year"))
                arr = model_stacked.data
                x = focus_event.sel(region=region).data
                probs_tmp = []
                for ii in range(n_iterations):
                    random_idxs = np.random.randint(0, arr.size, size=arr.size)
                    random_sample = arr[random_idxs]
                    prob = _calc_percentile(random_sample, x)
                    probs_tmp.append(prob)
                probs_years.append(probs_tmp)
            risks_bootstrapped.append(probs_years)

        risks_bootstrapped = xr.DataArray(
            risks_bootstrapped,
            [model_da["region"], pivot_years, np.arange(n_iterations) + 1],
            ["region", "year", "iteration"],
        )
        perc_low = risks_bootstrapped.quantile(quantile_low, dim="iteration")
        perc_high = risks_bootstrapped.quantile(quantile_high, dim="iteration")
        return perc_low, perc_high

    # core period
    print("Func-time bootstrapping (core period):")
    perc_low, perc_high = calc_bootstrap_quantiles(
        core_pivot_yrs, trend_source, extrapolated=False
    )

    # extrapolated period (optional)
    perc_low_extrapolated = None
    perc_high_extrapolated = None
    if extrapolated:
        if extrapolate_yrs is None:
            raise ValueError(
                "`extrapolate_yrs` array must be provided if extrapolated=True"
            )
        print("Func-time bootstrapping (extrapolated period):")
        perc_low_extrapolated, perc_high_extrapolated = calc_bootstrap_quantiles(
            extrapolate_yrs,
            "model",
            extrapolated=True,
            extrapolate_yrs=extrapolate_yrs,
        )

    return perc_low, perc_high, perc_low_extrapolated, perc_high_extrapolated
