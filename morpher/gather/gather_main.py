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

def processcmip(variable,pathway):
    # bring in the config variables

    latitude = parse('latitude')
    longitude = parse('longitude')

    gcsfs.GCSFileSystem(token='anon')
    col = intake.open_esm_datastore("https://storage.googleapis.com/cmip6/pangeo-cmip6.json") #TODO make local
    sl_df = pd.DataFrame(pd.read_csv(os.path.join(os.path.dirname(__file__), 'modelsources.csv')))
    sourcelist = sl_df[sl_df['in_ensemble'] == 'Yes']['source_id'].values.tolist()
    print('Gathering the ensemble members for variable - {}'.format(variable))
    query = dict(
        experiment_id=pathway,
        table_id='Amon',
        variable_id=variable,
        member_id='r1i1p1f1',
        source_id=sourcelist #TODO add an if for all
    )
    col_subset = col.search(require_all_on=["source_id"], **query)

    def drop_all_bounds(ds):
        drop_vars = [vname for vname in ds.coords
                     if (('_bounds') in vname) or ('_bnds') in vname]
        return ds.drop(drop_vars)

    def open_dset(df):
        data = xr.open_zarr(fsspec.get_mapper(df.zstore.values[0]), consolidated=True)

        if 'lat' in data.coords:
            data = data.sel(
                lat=latitude, lon=longitude, method='nearest')
        else:
            data = data.sel(
                latitude=latitude, longitude=longitude, method='nearest')

        data.coords['year'] = data.time.dt.year
        data.coords['time'] = xr.cftime_range(start=str(data.time.dt.year.values[0]),
                                            periods=len(data.time.dt.year.values),
                                            freq="MS", calendar="noleap")
        if 'historical' in pathway:
            data = data.sel(time=slice('1960', '2020'))
        else:
            data = data.sel(time=slice('2015', '2100'))
        return drop_all_bounds(data)

    def open_delayed(df):
        return dask.delayed(open_dset)(df)

    from collections import defaultdict
    dsets = defaultdict(dict)

    for group, df in tqdm.tqdm(col_subset.df.groupby(by=['source_id', 'experiment_id'])):
        # print(group)
        dsets[group[0]][group[1]] = open_delayed(df)

    print('')
    with progress.ProgressBar():
        dsets_ = dask.compute(dict(dsets))[0]

    # expt_da = xr.DataArray(pathway, dims='experiment_id', name='experiment_id',
    #                        coords={'experiment_id': pathway})

    dsets_aligned = {}

    for k, v in tqdm.tqdm(dsets_.items()):
        expt_dsets = v.values()
        if any([d is None for d in expt_dsets]):
            print(f"Missing experiment for {k}")
            continue

        for ds in expt_dsets:
            ds.coords['year'] = ds.time.dt.year #TODO Align all

        dsets_ann_mean = [v[pathway]]

        # align everything with the 4xCO2 experiment
        dsets_aligned[k] = xr.concat(dsets_ann_mean, join='outer',
                                     dim=pathway)

    with progress.ProgressBar():
        dsets_aligned_ = dask.compute(dsets_aligned)[0]

    source_ids = list(dsets_aligned_.keys())
    source_da = xr.DataArray(source_ids, dims='source_id', name='source_id',
                             coords={'source_id': source_ids})

    big_ds = xr.concat([ds.reset_coords(drop=True)
                        for ds in dsets_aligned_.values()],
                       dim=source_da)
    return big_ds

def createensemble(variable,pathway):
    """
    :param variable: the variable that is being worked on (e.g. tasmax)
    :return: a dictionary of xarrays for each percentile
             where key is percentile as integer (dict[15] : 15th percentile)
    """

    outputs = processcmip(variable,pathway)
    print('Beginning to process the ensemble for variable - {}'.format(variable))
    percentile_list = parse('percentiles').split(',')
    percentile_list = list(map(int, percentile_list))
    dataarray = getattr(outputs, variable)
    ens = ensembles.create_ensemble(dataarray)
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

    for varkey in variable_list:
        name = parse('project-name')
        path = os.path.join(os.pardir, 'output', '{}'.format(name), '{}'.format(pathway), '{}-{}.csv'.format(pathway, varkey))
        pdict = vardict[varkey]
        data = pd.DataFrame()

        for i in percentile_list:
            data[i] = pd.Series(pdict[i].values)

        data['date'] = pdict[percentile_list[0]].coords['time'].values
        data.to_csv(path, index=True)
        print('Variable  - {} saved.'.format(varkey))
    return print('All {} files saved.'.format(pathway))

def initialize_project():
    name = parse('project-name')
    print(os.pardir)
    if os.path.exists(os.path.join(os.pardir, 'output', '{}'.format(name))):
        for pathway in parse('pathwaylist').split(','):
            if os.path.exists(os.path.join(os.pardir, 'output', '{}'.format(name), '{}'.format(pathway))):
                print('{} exists, moving on.'.format(pathway))
                continue
            else:
                os.makedirs(os.path.join(os.pardir, 'output', '{}'.format(name), '{}'.format(pathway)))
                print('Downloading {} CMIP6 data.'.format(pathway))
                exportcmip(pathway)
    else:
        os.makedirs(os.path.join(os.pardir, 'output', '{}'.format(name)))
        print('Initializing project with historical CMIP6 data download.')
        os.makedirs(os.path.join(os.pardir, 'output', '{}'.format(name), 'historical'))
        exportcmip('historical')
        for pathway in parse('pathwaylist').split(','):
            os.makedirs(os.path.join(os.pardir, 'output', '{}'.format(name), '{}'.format(pathway)))
            print('Continuing with {} CMIP6 data download.'.format(pathway))
            exportcmip(pathway)
    return print('Climate model data has been downloaded.')

if __name__ == '__main__':
    initialize_project()