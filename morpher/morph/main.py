# coding=utf-8
"""
The primary moprhing script.
"""

# imports
import time
import morpher.morph.routine as morph
import morpher.gather.gather_main as gather

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

if __name__ == '__main__':
    startTime = time.time()
    begin()
    gather.initialize_project()
    morph.morph_main()
    end()
    print('The script took {0} second !'.format(time.time() - startTime))