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
from morpher.morph import routine
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
    longitude = parse('longitude')
    latitude = parse('latitude')


    year = (futurestart + futureend) / 2
    pathway, historical = process_modeldata.climatologies('50',
                                                          year)
    df = routine.morph_routine(weather_path, pathway, historical, longitude, latitude)

    manipulate_epw.out_epw(df, 2065)
    # year = (int(futurestart)+30 + int(futureend)+30) / 2
    # out_epw(fut_df, year, outputpath)
    df.to_csv(r"C:\Users\justi\Desktop\test.csv")
    return print(df.head(24))

if __name__ == '__main__':
    print(test())