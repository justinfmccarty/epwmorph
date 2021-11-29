# coding=utf-8
"""
Extracts details from the configuration file for guiding the morphing script.
"""

# imports
import configparser
import os

__author__ = "Justin McCarty"
__copyright__ = "Copyright 2020, justinmccarty"
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Justin McCarty"
__email__ = "mccarty.justin.f@gmail.com"
__status__ = "Production"

# set universal variables
config_file = os.path.join(os.path.dirname(__file__), 'user.config')

def parse(setting):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config["settings"][setting]

def parse_set(setting, value):
    config = configparser.ConfigParser()
    config.read(config_file)
    config.set('settings', setting, value)
    with open(config_file, 'w+') as configfile:
        config.write(configfile)
    return print('{} changed to {}'.format(setting, value))

# if __name__ == '__main__':
#     parse = parse()