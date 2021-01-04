# coding=utf-8
"""
Testing.
"""

# imports
from morpher.config import parse
import os
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
    name = parse('project-name')
    outputpath = parse('output')

    percentile_list = parse('percentiles').split(',')
    percentile_list = list(map(int, percentile_list))

    year_list = parse('yearlist').split(',')
    year_list = list(map(int, year_list))

    for ptile in percentile_list:
        print(ptile)
        year = year_list[0]
        pathway, historical = process_modeldata.climatologies(str(ptile), year, 5, 15)
        df = routine.morph_routine(weather_path, pathway, historical, longitude, latitude)
        filename = '{}_year_out.epw'.format(ptile,year)
        outputpath = os.path.join(os.pardir, 'output', '{}'.format(name), filename)
        manipulate_epw.out_epw(ptile, df, year, outputpath)

def test2():
    yearranges = parse('yearranges').split('|')
    for i in yearranges:
        print(int(list(i.split(','))[0]))
if __name__ == '__main__':
    test2()