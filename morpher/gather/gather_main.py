# coding=utf-8
"""
Query the CMIP6 google cloud for the ensemble of climate model output and package it for use in the the remainder of
the script.
"""

# imports
from morpher.config import parse
import os
from tqdm import tqdm
import xarray as xr
import tqdm
import intake
import gcsfs
import dask
from dask.diagnostics import progress
import fsspec
import pandas as pd
from xclim import ensembles

__author__ = "Justin McCarty"
__copyright__ = "Copyright 2020, justinmccarty"
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Justin McCarty"
__email__ = "mccarty.justin.f@gmail.com"
__status__ = "Production"

# set universal variables
config_file = os.path.join(os.path.dirname(__file__), 'default.config')


def processcmip(variable, pathway):
    latitude = float(parse('latitude'))
    longitude = float(parse('longitude'))

    gcsfs.GCSFileSystem(token='anon')
    col = intake.open_esm_datastore("https://storage.googleapis.com/cmip6/pangeo-cmip6.json")  # TODO make local
    sl_df = pd.DataFrame(pd.read_csv(parse('modelsources')))
    sourcelist = sl_df[sl_df['in_ensemble'] == 'Yes']['source_id'].values.tolist()
    print('Gathering the ensemble members for variable - {}'.format(variable))

    cat = col.search(experiment_id=pathway,  # pick the `historical` forcing experiment
                     table_id='Amon',  # choose to look at atmospheric variables (A) saved at monthly resolution (mon)
                     variable_id=variable,
                     # choose to look at near-surface air temperature (tas) as our variable
                     member_id='r1i1p1f1',
                     source_id=sourcelist)  # arbitrarily pick one realization for each model (i.e. just one set of initial conditions)

    # convert data catalog into a dictionary of xarray datasets
    dset_dict = cat.to_dataset_dict(zarr_kwargs={'consolidated': True, 'decode_times': False})

    ds_dict = {} # set the blank dict for the datasets to be placed in keyed by source_id
    for name, ds in tqdm.tqdm(dset_dict.items()):
        print(name)
        # rename spatial dimensions if necessary
        if ('longitude' in ds.dims) and ('latitude' in ds.dims):
            ds = ds.rename({'longitude': 'lon', 'latitude': 'lat'})  # some models labelled dimensions differently...

        ds = xr.decode_cf(ds)  # temporary hack, not sure why I need this but has to do with calendar-aware metadata on the time variable

        if 'historical' in pathway:
            ds = ds.sel(time=slice('1960', '2014'))
        else:
            ds = ds.sel(time=slice('2015', '2100'))

        ds = ds.sel(lat=latitude, lon=longitude, method='nearest')

        # drop redundant variables (like "height: 2m")
        for coord in ds.coords:
            if coord not in ['lat', 'lon', 'time']:
                ds = ds.drop(coord)

        ds.coords['year'] = ds.time.dt.year
        ds.coords['time'] = xr.cftime_range(start=str(ds.time.dt.year.values[0]),
                                            periods=len(ds.time.dt.year.values),
                                            freq="MS", calendar="noleap")

        # Add variable array to dictionary
        ds_dict[name] = ds

    with progress.ProgressBar():
        dsets_aligned_ = dask.compute(ds_dict)[0]

    return dsets_aligned_

def createensemble(variable,pathway):
    """
    :param variable: the variable that is being worked on (e.g. tasmax)
    :return: a dictionary of xarrays for each percentile
             where key is percentile as integer (dict[15] : 15th percentile)
    """

    print('Beginning to process the ensemble for variable - {}'.format(variable))
    percentile_list = parse('percentiles').split(',')
    percentile_list = list(map(int, percentile_list))
    data = processcmip(variable,pathway)
    ens = ensembles.create_ensemble([ds.reset_coords(drop=True) for ds in data.values()])
    ens_perc = ensembles.ensemble_percentiles(ens, values=percentile_list, split=False)
    # ens_stats = ensembles.ensemble_mean_std_max_min(ens)
    percentile_dict = dict()
    for ptilekey in percentile_list:
        print('Creating ensemble for {}-{}th percentile'.format(pathway,ptilekey))
        percentile_dict.update({ptilekey: getattr(ens_perc, variable).sel(percentiles=ptilekey)[0]})
    return percentile_dict

def gathercmipmain(pathway):
    """
    processes the cmip6 cloud query and the ensemble creator for each variable returning a dictionary of dictionaries
    :return: a dictionary where keys are variables and return subdictionaries for each percentile being computed
    """

    variable_list = parse('variables').split(',')
    variable_dict = dict()
    for varkey in variable_list:
        variable_dict.update({varkey: createensemble(varkey,pathway)})
        print('Creating dictionary member for variable - {}.'.format(varkey))
    print('Returning a dictionary for each variable with subdictionaires for each percentile.')
    return variable_dict

def exportcmip(pathway):
    """
    Exports the percentile dict to a csv
    :return: csv
    """

    percentile_list = parse('percentiles').split(',')
    percentile_list = list(map(int, percentile_list))
    variable_list = parse('variables').split(',')


    vardict = gathercmipmain(pathway)
    # TODO parallelize from here (per each scenario or hist open thread per variable)
    for varkey in variable_list:
        output_path = parse('output')
        path = os.path.join(output_path, f'{pathway}', f'{pathway}-{varkey}.csv')
        pdict = vardict[varkey]
        data = pd.DataFrame()

        for i in percentile_list:
            data[i] = pd.Series(pdict[i].values)

        data['date'] = pdict[percentile_list[0]].coords['time'].values
        data.to_csv(path, index=True)
        print(f'Variable  - {varkey} saved.')
    return print(f'All {pathway} files saved.')

def initialize_project():
    output_path = parse('output')
    print(os.pardir)
    if os.path.exists(output_path):
        for pathway in parse('pathwaylist').split(','):
            if os.path.exists(os.path.join(output_path, pathway)):
                print(f'{pathway} exists, moving on.')
                continue
            else:
                os.makedirs(os.path.join(output_path, pathway))
                print(f'Downloading {pathway} CMIP6 data.')
                exportcmip(pathway)
    else:
        os.makedirs(output_path)
        print('Initializing project with historical CMIP6 data download.')
        os.makedirs(os.path.join(output_path, 'historical'))
        exportcmip('historical')
        for pathway in parse('pathwaylist').split(','):
            os.makedirs(os.path.join(output_path, pathway))
            print(f'Continuing with {pathway} CMIP6 data download.')
            exportcmip(pathway)
    return print('Climate model data has been downloaded.')

if __name__ == '__main__':
    initialize_project()