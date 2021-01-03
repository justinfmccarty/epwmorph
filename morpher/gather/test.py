# coding=utf-8
"""
Testing.
"""

# imports
from morpher.config import parse
import gather_main
from xclim import ensembles
from epw import epw
import datetime as dt
import pandas as pd
from morpher.utilities import util
from morpher.process import manipulate_epw
from morpher.process import process_modeldata
import morpher.morph.procedures as mm
__author__ = "Justin McCarty"
__copyright__ = "Copyright 2020, justinmccarty"
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Justin McCarty"
__email__ = "mccarty.justin.f@gmail.com"
__status__ = "Production"

def test():
    weather_path = parse('epw')
    futurestart = parse('futurestart')
    futureend = parse('futureend')





    def morph_routine(future_climatolgy, historical_climatology):
        orig_epw = manipulate_epw.epw_to_dataframe(weather_path)
        orig_epw.index = pd.to_datetime(orig_epw.apply(lambda row: dt.datetime(2011,
                                                                               int(row.month),
                                                                               int(row.day),
                                                                               int(row.hour) - 1,
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

        # fut_df = fromdict?
        return fut_df

    pathway, historical = process_modeldata.climatologies('50',
                                                          int(futurestart) + 30,
                                                          int(futureend) + 30)

    morph_routine(pathway, historical)
    # year = (int(futurestart)+30 + int(futureend)+30) / 2
    # out_epw(fut_df, year, outputpath)
    return print()




    
    
if __name__ == '__main__':
    print(test())