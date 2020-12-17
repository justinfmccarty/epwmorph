# coding=utf-8
"""
Testing.
"""

# imports
from morpher.config import parse
import gather_main
from xclim import ensembles
import os


__author__ = "Justin McCarty"
__copyright__ = "Copyright 2020, justinmccarty"
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Justin McCarty"
__email__ = "mccarty.justin.f@gmail.com"
__status__ = "Production"

def create_ens(variable):
    """
    :param variable: the variable that is being worked on (e.g. tasmax)
    :return: a dictionary of xarrays for each percentile
             where key is percentile as integer (dict[15] : 15th percentile)
    """

    # outputs = gather_main.processcmip(variable)
    # print('Beginning to process the ensemble for variable - {}'.format(variable))
    # percentile_list = [15,65 ]
    # dataarray = getattr(outputs, variable)
    # print(dataarray)
    # ens = ensembles.create_ensemble(dataarray)
    # print(ens)
    # ens_perc = ensembles.ensemble_percentiles(ens, values=[15,65], split=False)
    # # ens_stats = ensembles.ensemble_mean_std_max_min(ens)
    # percentile_dict = dict()
    # for ptilekey in percentile_list:
    #     print('Creating ensemble for {}th percentile'.format(ptilekey))
    #     percentile_dict.update({ptilekey: ens_perc.tas.sel(percentiles=ptilekey)[0]})
    # return percentile_dict

def process():
    import os
    import pandas as pd
    test = pd.DataFrame()
    name = parse('project-name')
    os.makedirs(os.path.join(os.pardir,'output', '{}'.format(name)),exist_ok=True)
    path = os.path.join(os.pardir,'output', '{}'.format(name), "myfile.csv")
    test.to_csv(path)
    
    
if __name__ == '__main__':
    process()