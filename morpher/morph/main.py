# coding=utf-8
"""
The primary moprhing script.
"""

# imports
import time
import sys
import morpher.morph.routine as morph
import morpher.gather.gather_main as gather
import pandas as pd
from morpher.utilities import util
from morpher.utilities import call_uwg
from morpher.config import parse
import os
from morpher.config import parse_set

__author__ = "Justin McCarty"
__copyright__ = "Copyright 2020, justinmccarty"
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Justin McCarty"
__email__ = "mccarty.justin.f@gmail.com"
__status__ = "Production"


def begin():
    if parse('output')=='':
        new_output = os.path.join(os.pardir, 'output', parse('project-name'))
        parse_set('output', new_output)
        print(f'Set project output folder at {new_output}')
    else:
        print(f"Output will be saved to {os.path.join(parse('output'))}")
    return print('---Beginning morphing routine.---')

def end():
    print('---All processes completed.---')
    return print(f"Look for results in {os.path.join(parse('output'))}")


def run():
    # check for Urban Weather Generator
    if parse('uwg')=='Only':
        print('Running UWG script and then exiting protocol')
        call_uwg.run_UWG()
        sys.exit()
    elif parse('uwg')=='True':
        print('Running UWG script and then continuing to morph')
        call_uwg.run_UWG()
    else:
        pass

    if parse('loop')=='True':
        settings_df = pd.DataFrame(pd.read_csv(os.path.join(parse('epwdir'),'epwlist.csv')))
        for row in list(range(len(settings_df))):
            if settings_df['completed'][row]=='Yes':
                pass
            else:
                util.set_config_loop(row)
                print('Starting {}'.format(parse('project-name')))
                begin()
                gather.initialize_project()
                morph.morph_main()
                end()
                settings_df['completed'][row] = 'Yes'
    else:
        begin()
        gather.initialize_project()
        morph.morph_main()
        end()

def query(epw_orig_path):
    record = pd.read_csv(epw_orig_path,skiprows=3).iloc[1,1]
    print(record)
    record_years_start = record.split('=')[2].split(';')[0].split('-')[0]
    record_years_end = record.split('=')[2].split(';')[0].split('-')[1]
    return record_years_start, record_years_end

if __name__ == '__main__':
    startTime = time.time()
    run()
    print('The script took {0} second !'.format(time.time() - startTime))