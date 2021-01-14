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
    orig_epw = manipulate_epw.epw_to_dataframe(weather_path)
    year = int(orig_epw['year'][0:1].values)
    orig_epw.index = pd.to_datetime(orig_epw.apply(lambda row: dt.datetime(year,
                                                                           int(row.month),
                                                                           int(row.day),
                                                                           int(row.hour),
                                                                           int(row.minute)), axis=1))
    fut = future_climatolgy
    hist = historical_climatology
    dbt = mm.morph_dbt(orig_epw,
                       fut['tas'].values,
                       hist['tas'].values,
                       fut['tasmax'].values,
                       hist['tasmax'].values,
                       fut['tasmin'].values,
                       hist['tasmin'].values).values
    hurs = mm.morph_relhum(orig_epw, fut['huss'], hist['huss']).values
    psl = mm.morph_psl(orig_epw, fut['psl'], hist['psl']).values
    dewpt = mm.morph_dewpt(dbt, hurs)
    glohor = mm.morph_glohor(orig_epw, fut['rsds'], hist['rsds'])

    data = {"drybulb_C": dbt,
            "relhum_percent": hurs,
            "atmos_Pa": psl,
            "dewpoint_C": dewpt,
            "glohorrad_Whm2": glohor.values}

    fut_df = pd.DataFrame.from_dict(data)
    idx = pd.date_range('{}-01-01'.format(year), '{}-01-01'.format(year + 1), freq='1H')
    idx = idx[0:8760]
    fut_df['dayofyear'] = idx.dayofyear
    fut_df['hour'] = idx.hour

    clearness, clearness_day_list = util.calc_clearness(fut_df['glohorrad_Whm2'], orig_epw['exthorrad_Whm2'])
    fut_df['hourly_clearness'] = clearness
    hourly_clearness_list = clearness.tolist()

    fut_df['daily_clearness'] = fut_df['dayofyear'].map(clearness_day_list)
    fut_df['rise_set'] = util.calc_rise_set(orig_epw, float(latitude), float(longitude))
    fut_df['row_number'] = fut_df.reset_index(drop=True).index.tolist()
    fut_df['row_number'] = fut_df['row_number'].astype(int)
    fut_df['persisted_index'] = fut_df.apply(lambda x: util.persistence(hourly_clearness_list,
                                                                        x['rise_set'],
                                                                        x['row_number']), axis=1)
    diffhor = mm.calc_diffhor(fut_df, longitude, latitude)
    fut_df['difhorrad_Whm2'] = diffhor.values
    dirnor = mm.calc_dirnor(fut_df)
    fut_df['dirnorrad_Whm2'] = dirnor.values
    tsc = mm.calc_tsc(orig_epw, fut['clt'], hist['clt'])
    fut_df['totskycvr_tenths'] = tsc.values
    osc = mm.calc_osc(orig_epw, fut_df)
    fut_df['opaqskycvr_tenths'] = osc.values
    wspd = mm.morph_wspd(orig_epw, future_climatolgy, historical_climatology)
    fut_df['windspd_ms'] = wspd.values
    dataframe_path = os.path.join(os.pardir, 'output', '{}'.format(parse('project-name')), pathway, 'EPWs')
    fut_df.to_csv(os.path.join(dataframe_path, 'calculations.csv'))
    return fut_df

def morph_main():
    weather_path = parse('epw')
    longitude = parse('longitude')
    latitude = parse('latitude')
    name = parse('project-name')
    # outputpath = parse('output')


    for pathway in parse('pathwaylist').split(','):
        outputpath = os.path.join(os.pardir, 'output', '{}'.format(name), pathway, 'EPWs')
        if os.path.exists(outputpath):
            pass
        else:
            os.makedirs(outputpath)
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
                out = os.path.join(outputpath, filename)
                manipulate_epw.out_epw(ptile, df, year, out, pathway)

    return print('Morphing completed.')

if __name__ == '__main__':
    morph_main()