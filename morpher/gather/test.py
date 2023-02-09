# coding=utf-8
"""
Testing.
"""

# imports
from morpher.config import parse
from morpher.config import parse_set
import time
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



def test2():
    # print(parse('elevation(m)'))
    # parse_set('elevation(m)', '90')
    startTime = time.time()
    # Your code here !
    util.build_epw_list()
    print(con)
    print('The script took {0} second !'.format(time.time() - startTime))

def view_epw():
    import gcsfs


if __name__ == '__main__':
    view_epw()