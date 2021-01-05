# coding=utf-8
"""
The primary moprhing script.
"""

# imports
import time
import morpher.morph.routine as morph
import morpher.gather.gather_main as gather
import pandas as pd
from morpher.utilities import util
from morpher.config import parse
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
    return print('Beginning morphing routine.')

def end():
    return (print('All processes completed.'))

def run():
    if parse('loop')=='True':
        settings_df = pd.DataFrame(pd.read_csv(parse('loop_settings_file')))
        for row in list(range(len(settings_df))):
            util.set_config_loop(row)
            print(parse('project-name'))
            begin()
            # gather.initialize_project()
            # morph.morph_main()
            end()
    else:
        begin()
        # gather.initialize_project()
        # morph.morph_main()
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