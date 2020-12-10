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
import gcsfs
import tqdm
import intake
import dask
from dask.diagnostics import progress
import fsspec

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

def processcmip(variable):
    # bring in the config variables
    pathway = parse('pathway')
    latitude = parse('latitude')
    longitude = parse('longitude')

    gcs = gcsfs.GCSFileSystem(token='anon')
    col = intake.open_esm_datastore("https://storage.googleapis.com/cmip6/pangeo-cmip6.json")

    query = dict(
        experiment_id=pathway,
        table_id='Amon',
        variable_id=variable,
        member_id='r1i1p1f1',
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
            data = data.sel(time=slice('1980', '2020'))
        else:
            data = data.sel(time=slice('2020', '2100'))
        return drop_all_bounds(data)

    def open_delayed(df):
        return dask.delayed(open_dset)(df)

    from collections import defaultdict
    dsets = defaultdict(dict)

    for group, df in tqdm.tqdm(col_subset.df.groupby(by=['source_id', 'experiment_id'])):
        # print(group)
        dsets[group[0]][group[1]] = open_delayed(df)

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
            ds.coords['year'] = ds.time.dt.year

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

if __name__ == '__main__':
    processcmip()