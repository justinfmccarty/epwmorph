import time
import morpher.morph.routine as morph
import morpher.gather.gather_main as gather
import pandas as pd
from morpher.utilities import util
from morpher.config import parse
import os
from uwg import UWG
from morpher.config import parse_set
from morpher.process import manipulate_epw as mepw
import intake


def test_config():
    if parse('output')=='':
        name = parse('project-name')
        print(os.path.join(os.pardir, 'output', '{}'.format(name), 'ssp126', 'EPWs'))
    else:
        print(os.path.join(parse('output'),'ssp126','EPWs'))

    parse_set('output','Hello Path')

def run_UWG():
    # Define the .epw, .uwg paths to create an uwg object.
    sg_path = "/Users/jmccarty/Desktop/adam_chris_morphed/SG/SG_standard.epw"
    zh_path = "/Users/jmccarty/Desktop/adam_chris_morphed/ZH/zurich_standard.epw"

    # Initialize the UWG model by passing parameters as arguments, or relying on defaults

    # sg model params from https://doi.org/10.1016/j.uclim.2014.05.005 Table 1 (Tampines)
    sg_model = UWG.from_param_args(epw_path=sg_path,
                                   bldheight=36,
                                   blddensity=0.29,
                                   vertohor=1.66,
                                   grasscover=0.2,
                                   treecover=0.14,
                                   zone='1A',
                                   new_epw_name='sg_new.epw')

    zh_model = UWG.from_param_args(epw_path=zh_path,
                                   bldheight=14.6,
                                   blddensity=0.4,
                                   vertohor=1.1,
                                   grasscover=0.1,
                                   treecover=0.2,
                                   zone='4A',
                                   new_epw_name='zh_new.epw')
    for model in [sg_model, zh_model]:
        model.generate()
        model.simulate()

        # Write the simulation result to a file.
        model.write_epw()


if __name__ == '__main__':
    startTime = time.time()
    url = "https://storage.googleapis.com/cmip6/pangeo-cmip6.json"
    col = intake.open_esm_datastore('/Users/jmccarty/GitHub/epwmorph/morpher/gather/cloud_resources/pangeo-cmip6.json')
    print(col.df.head())
    print('The script took {0} second !'.format(time.time() - startTime))
