# coding=utf-8
"""
General utility functions, solar geometry calculations, and meteorological calculations.
"""

# imports
import os
import shutil
from morpher.config import parse

def export_config():
    directory = os.path.split(os.path.abspath(__file__))[0].split('/utilities')[0]
    source = os.path.join(directory,'user.config')
    destination = os.path.dirname(parse('output'))
    shutil.copy2(source, destination)
    print(f"Copied user configuration file to {destination}.")

if __name__ == '__main__':
    export_config()