# coding=utf-8
"""
Testing.
"""

# imports
from morpher.config import parse
import gather_main
from xclim import ensembles
from epw import epw


__author__ = "Justin McCarty"
__copyright__ = "Copyright 2020, justinmccarty"
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Justin McCarty"
__email__ = "mccarty.justin.f@gmail.com"
__status__ = "Production"

def test(path):
    a = epw()
    a.read(path)
    return print(a.dataframe)
    
    
if __name__ == '__main__':
    test(r"C:\Users\justi\Dropbox\Architecture_Design\Data\EPWs\3_Present\CAN_BC_Vancouver.Intl.AP.718920_CWEC2016\CAN_BC_Vancouver.Intl.AP.718920_CWEC2016.epw")