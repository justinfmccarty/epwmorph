import os
import pandas as pd
import datetime as dt
import util
import morph_procedures as mm


def calc_model_climatologies(config_dict, variable_dict, variable, percentile,
                             future_range, pathway):
    baseline_start = config_dict['baseline_start']
    baseline_end = config_dict['baseline_end']
    future_start = future_range[0]
    future_end = future_range[1]

    hist_init = pd.DataFrame(variable_dict[f"historical_{variable}"]['df'])[[percentile, 'date']]
    hist_init['date'] = pd.to_datetime(hist_init['date'])
    hist_init = hist_init.set_index('date')
    hist_init = hist_init['{}-01-01'.format(baseline_start):'{}-12-01'.
        format(baseline_end)]
    hist_init = hist_init.groupby(hist_init.index.month).mean()
    hist_init = pd.Series(hist_init[percentile]).rename(variable)

    var_init = pd.DataFrame(variable_dict[f"{pathway}_{variable}"]['df'])[[percentile, 'date']]
    var_init['date'] = pd.to_datetime(var_init['date'])
    var_init = var_init.set_index('date')
    var_init = var_init['{}-01-01'.format(future_start):'{}-12-01'.
        format(future_end)]
    var_init = var_init.groupby(var_init.index.month).mean()
    var_init = pd.Series(var_init[percentile]).rename(variable)

    return var_init, hist_init


def climatologies(config_dict, variable_dict, percentile, future_range,
                  pathway):
    variable_list = config_dict['download_variables']
    historical_df = pd.DataFrame()
    pathway_df = pd.DataFrame()
    for variable in variable_list:
        print(variable)
        fut_variable, hist_variable = calc_model_climatologies(
            config_dict, variable_dict, variable, str(percentile), future_range,
            pathway)
        historical_df[variable] = pd.Series(hist_variable)
        pathway_df[variable] = pd.Series(fut_variable)
    return pathway_df, historical_df


def morph_tmy(tmy_df, future_climatolgy, historical_climatology, config_dict):
    variables = config_dict['variables']

    longitude = config_dict['longitude']
    latitude = config_dict['latitude']
    year = int(tmy_df['year'][0:1].values)
    tmy_df.index = pd.to_datetime(
        tmy_df.apply(lambda row: dt.datetime(year, int(row.month), int(
            row.day), int(row.hour), int(row.minute)),
                     axis=1))
    if "tas" in variables:
        print("temp detected in variables, morphing temp")
        dbt = mm.morph_dbt(tmy_df, future_climatolgy['tas'].values,
                           historical_climatology['tas'].values,
                           future_climatolgy['tasmax'].values,
                           historical_climatology['tasmax'].values,
                           future_climatolgy['tasmin'].values,
                           historical_climatology['tasmin'].values).values
    else:
        print("temp NOT detected in variables, using original temp")
        dbt = tmy_df['drybulb_C'].values

    if "huss" in variables:
        print("humidity detected in variables, morphing humidity")
        hurs = mm.morph_relhum(tmy_df, future_climatolgy['huss'],
                               historical_climatology['huss']).values
    else:
        print("humidity NOT detected in variables, using original humidity")
        hurs = tmy_df['relhum_percent'].values

    if "psl" in variables:
        print("pressure detected in variables, morphing pressure")
        psl = mm.morph_psl(tmy_df, future_climatolgy['psl'],
                           historical_climatology['psl']).values
    else:
        print("pressure NOT detected in variables, using original pressure")
        psl = tmy_df['atmos_Pa'].values

    print("setting dew point using drybulb temp and humidity")
    dewpt = mm.morph_dewpt(dbt, hurs)

    if "clt" in variables:
        print("Cloud cover detected in variables, morphing global horizontal")
        glohor = mm.morph_glohor(tmy_df, future_climatolgy['rsds'],
                                 historical_climatology['rsds'])
    else:
        print("Cloud cover NOT detected in variables, using original global horizontal")
        glohor = tmy_df['glohorrad_Whm2']

    data = {
        "drybulb_C": dbt,
        "relhum_percent": hurs,
        "atmos_Pa": psl,
        "dewpoint_C": dewpt,
        "glohorrad_Whm2": glohor.values
    }

    fut_df = pd.DataFrame.from_dict(data)
    idx = pd.date_range('{}-01-01'.format(year),
                        '{}-01-01'.format(year + 1),
                        freq='1H')
    idx = idx[0:8760]
    fut_df['dayofyear'] = idx.dayofyear
    fut_df['hour'] = idx.hour

    clearness, clearness_day_list = util.calc_clearness(
        fut_df['glohorrad_Whm2'], tmy_df['exthorrad_Whm2'])
    fut_df['hourly_clearness'] = clearness
    hourly_clearness_list = clearness.tolist()

    fut_df['daily_clearness'] = fut_df['dayofyear'].map(clearness_day_list)
    fut_df['rise_set'] = util.calc_rise_set(tmy_df, float(latitude),
                                            float(longitude))
    fut_df['row_number'] = fut_df.reset_index(drop=True).index.tolist()
    fut_df['row_number'] = fut_df['row_number'].astype(int)
    fut_df['persisted_index'] = fut_df.apply(lambda x: util.persistence(
        hourly_clearness_list, x['rise_set'], x['row_number']),
                                             axis=1)

    if "clt" in variables:
        print("Cloud cover detected in variables, morphing diffuse horizontal")
        diffhor = mm.calc_diffhor(fut_df, config_dict, longitude, latitude)
        fut_df['difhorrad_Whm2'] = diffhor.values
        print("Cloud cover detected in variables, morphing direct normal")
        dirnor = mm.calc_dirnor(fut_df)
        fut_df['dirnorrad_Whm2'] = dirnor.values
    else:
        print("Cloud cover NOT detected in variables, using original diffuse horizontal")
        fut_df['difhorrad_Whm2'] = tmy_df['difhorrad_Whm2'].values
        print("Cloud cover NOT detected in variables, using original direct normal")
        fut_df['dirnorrad_Whm2'] = tmy_df['dirnorrad_Whm2'].values

    if "clt" in variables:
        print("Cloud cover detected in variables, morphing sky cover")
        tsc = mm.calc_tsc(tmy_df, future_climatolgy['clt'],
                          historical_climatology['clt'])
        fut_df['totskycvr_tenths'] = tsc.values

        osc = mm.calc_osc(tmy_df, fut_df)
        fut_df['opaqskycvr_tenths'] = osc.values
    else:
        print("Cloud cover NOT detected in variables, using original sky cover")
        fut_df['totskycvr_tenths'] = tmy_df['totskycvr_tenths'].values
        fut_df['opaqskycvr_tenths'] = tmy_df['opaqskycvr_tenths'].values

    if "vas" in variables:
        print("wind detected in variables, morphing wind")
        wspd = mm.morph_wspd(tmy_df, future_climatolgy, historical_climatology)
        fut_df['windspd_ms'] = wspd.values
    else:
        print("wind NOT detected in variables, using original wind")
        fut_df['windspd_ms'] = tmy_df['windspd_ms'].values

    return fut_df