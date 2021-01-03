# coding=utf-8
"""
Open the outputs from the model ensemble and calculate climatologies to be referenced for the morphing process.
"""

# imports
from morpher.config import parse
import os
import pandas as pd

__author__ = "Justin McCarty"
__copyright__ = "Copyright 2020, justinmccarty"
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Justin McCarty"
__email__ = "mccarty.justin.f@gmail.com"
__status__ = "Production"

def calc_model_climatologies(var, percentile, futurestart, futureend):

    name = parse('project-name')
    pathway = parse('pathway')
    baselinestart = parse('baselinestart')
    baselineend = parse('baselineend')

    hist_path = os.path.join(os.pardir, 'output', '{}'.format(name), 'historical-{}.csv'.format(var))
    var_path = os.path.join(os.pardir, 'output', '{}'.format(name), '{}-{}.csv'.format(pathway, var))

    hist_init = pd.DataFrame(pd.read_csv(hist_path, usecols=[percentile,'date']))
    hist_init['date'] = pd.to_datetime(hist_init['date'])
    hist_init = hist_init.set_index('date')
    hist_init = hist_init['{}-01-01'.format(baselinestart) :'{}-12-01'.format(baselineend)]
    hist_init = hist_init.groupby(hist_init.index.month).mean()
    hist_init = pd.Series(hist_init[percentile]).rename(var)

    var_init = pd.DataFrame(pd.read_csv(var_path, usecols=[percentile,'date']))
    var_init['date'] = pd.to_datetime(var_init['date'])
    var_init = var_init.set_index('date')
    var_init = var_init['{}-01-01'.format(futurestart) :'{}-12-01'.format(futureend)]
    var_init = var_init.groupby(var_init.index.month).mean()
    var_init = pd.Series(var_init[percentile]).rename(var)

    return var_init, hist_init

def climatologies(percentile, futurestart, futureend):
    variable_list = parse('variables').split(',')
    historical = pd.DataFrame()
    pathway = pd.DataFrame()
    for var in variable_list:
        fut_var, hist_var = calc_model_climatologies(var, percentile, futurestart, futureend)
        historical[var] = pd.Series(hist_var)
        pathway[var] = pd.Series(fut_var)
    return pathway, historical