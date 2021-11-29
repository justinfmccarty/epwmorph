import time
import sys
import morpher.morph.routine as morph
import morpher.gather.gather_main as gather
import pandas as pd
from morpher.utilities import util
from morpher.config import parse
import os
from epw import epw # https://github.com/building-energy/epw
from uwg import UWG
from morpher.config import parse_set
from morpher.process import manipulate_epw



def run_UWG():
    # Initialize the UWG model by passing parameters file as arguments, or relying on defaults
    if 'UWG' in parse('epw'):
        print("ATTENTION: \n"
              " Current weather file is suspected to already be UWG because 'UWG' in file name. \n"
              " Stopping script. \n"
              " Remove 'UWG' from file name to continue with file or use different EPW.")
        sys.exit()

    param_path = parse('uwg_params_path')  # available in resources directory.
    model = UWG.from_param_file(param_path, epw_path=parse('epw'))
    model.generate()
    model.simulate()

    # Write the simulation result to a file.
    model.write_epw()

    # fix the UWG formatting
    uwg_df = manipulate_epw.epw_to_dataframe(model.new_epw_path,urban=True)
    a = manipulate_epw.edit_epw(uwg_df,year=None)
    a.write(model.new_epw_path)

    # change the config file epw path
    parse_set('epw', model.new_epw_path)

if __name__ == '__main__':
    startTime = time.time()
    run_UWG()
    print(f'Urban Weather Generator took {time.time() - startTime} second !')