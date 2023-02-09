# coding=utf-8
"""
Sequence of the morphing routines returning a messy dataframe with the new series and solar geometry calculations.
"""

# imports

import datetime as dt
from morpher.config import parse
from morpher.process import process_modeldata
import os
import pandas as pd
from morpher.utilities import util
from morpher.process import manipulate_epw
import morpher.morph.procedures as mm
__author__ = "Justin McCarty"
__copyright__ = "Copyright 2020, justinmccarty"
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Justin McCarty"
__email__ = "mccarty.justin.f@gmail.com"
__status__ = "Production"


def morph_routine(weather_path, future_climatolgy, historical_climatology, longitude, latitude, pathway):
    tmy_df = manipulate_epw.epw_to_dataframe(weather_path, urban=parse('uwg'))
    variables = parse('variables')

    year = int(tmy_df['year'][0:1].values)
    tmy_df.index = pd.to_datetime(tmy_df.apply(lambda row: dt.datetime(year,
                                                                           int(row.month),
                                                                           int(row.day),
                                                                           int(row.hour),
                                                                           int(row.minute)), axis=1))
    fut = future_climatolgy
    hist = historical_climatology
    ### temp
    if "tas" in variables:
        print("temp detected in variables, morphing temp")
        dbt = mm.morph_dbt(tmy_df,
                           fut['tas'].values,
                           hist['tas'].values,
                           fut['tasmax'].values,
                           hist['tasmax'].values,
                           fut['tasmin'].values,
                           hist['tasmin'].values).values
    else:
        print("temp NOT detected in variables, using original temp")
        dbt = tmy_df['drybulb_C'].values

    ### humidity
    if "huss" in variables:
        print("humidity detected in variables, morphing humidity")
        hurs = mm.morph_relhum(tmy_df, fut['huss'], hist['huss']).values
    else:
        print("humidity NOT detected in variables, using original humidity")
        hurs = tmy_df['relhum_percent'].values

    ### pressure
    if "psl" in variables:
        print("pressure detected in variables, morphing pressure")
        psl = mm.morph_psl(tmy_df, fut['psl'], hist['psl']).values
    else:
        print("pressure NOT detected in variables, using original pressure")
        psl = tmy_df['atmos_Pa'].values

    ### dew point
    print("Resetting dew point using drybulb temp and humidity")
    dewpt = mm.morph_dewpt(dbt, hurs)

    ### irradiance
    if "clt" in variables:
        print("irradiance detected in variables, morphing global horizontal")
        glohor = mm.morph_glohor(tmy_df, fut['rsds'], hist['rsds'])
    else:
        print("irradiance NOT detected in variables, using original global horizontal")
        glohor = tmy_df['glohorrad_Whm2']

    data = {"drybulb_C": dbt,
            "relhum_percent": hurs,
            "atmos_Pa": psl,
            "dewpoint_C": dewpt,
            "glohorrad_Whm2": glohor.values}

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
        hourly_clearness_list,x['rise_set'],x['row_number']),
                                             axis=1)

    ### diff hor irrad
    if "clt" in variables:
        print("irradiance detected in variables, morphing diffuse horizontal")
        diffhor = mm.calc_diffhor(fut_df, longitude, latitude)
        fut_df['difhorrad_Whm2'] = diffhor.values
        print("irradiance detected in variables, morphing direct normal")
        dirnor = mm.calc_dirnor(fut_df)
        fut_df['dirnorrad_Whm2'] = dirnor.values
    else:
        print("irradiance NOT detected in variables, using original diffuse horizontal")
        fut_df['difhorrad_Whm2'] = tmy_df['difhorrad_Whm2'].values
        print("irradiance NOT detected in variables, using original direct normal")
        fut_df['dirnorrad_Whm2'] = tmy_df['dirnorrad_Whm2'].values

    ### total sky cover
    if "clt" in variables:
        print("irradiance detected in variables, morphing sky cover")
        tsc = mm.calc_tsc(tmy_df, fut['clt'], hist['clt'])
        fut_df['totskycvr_tenths'] = tsc.values
        osc = mm.calc_osc(tmy_df, fut_df)
        fut_df['opaqskycvr_tenths'] = osc.values
    else:
        print("irradiance NOT detected in variables, using original sky cover")
        fut_df['totskycvr_tenths'] = tmy_df['totskycvr_tenths'].values
        fut_df['opaqskycvr_tenths'] = tmy_df['opaqskycvr_tenths'].values

    if "vas" in variables:
        print("wind detected in variables, morphing wind")
        wspd = mm.morph_wspd(tmy_df, future_climatolgy, historical_climatology)
        fut_df['windspd_ms'] = wspd.values
    else:
        print("wind NOT detected in variables, using original wind")
        fut_df['windspd_ms'] = tmy_df['windspd_ms'].values
    fut_df.to_csv(os.path.join(parse('output'), pathway, 'EPWs', 'calculations.csv'))
    return fut_df

def morph_main():
    weather_path = parse('epw')
    longitude = parse('longitude')
    latitude = parse('latitude')
    output_config = parse('output')


    for pathway in parse('pathwaylist').split(','):
        if pathway=='historical':
            pass
        else:
            epw_outputpath = os.path.join(output_config, pathway, 'EPWs')

            if os.path.exists(epw_outputpath):
                pass
            else:
                os.makedirs(epw_outputpath)
            print(pathway)
            for ptile in list(map(int, parse('percentiles').split(','))):
                print(str(ptile) + 'th Percentile')
                for i in parse('yearranges').split('|'):
                    print(i)
                    start = int(list(i.split(','))[0])
                    end = int(list(i.split(','))[1])
                    year = int((start + end) / 2)
                    pathway_df, historical_df = process_modeldata.climatologies(str(ptile), start, end, pathway)
                    df = morph_routine(weather_path, pathway_df, historical_df, longitude, latitude, pathway)
                    filename = '{}_{}_{}-{}.epw'.format(pathway,ptile,start,end)
                    out = os.path.join(epw_outputpath, filename)
                    manipulate_epw.out_epw(ptile, df, out, pathway, year=year)

    return print('Morphing completed.')

if __name__ == '__main__':
    morph_main()