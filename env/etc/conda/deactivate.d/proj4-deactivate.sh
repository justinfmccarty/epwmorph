#!/bin/sh

# Restore previous env vars if they were set.
unset PROJ_LIB
unset PROJ_NETWORK

if [ -n "$_CONDA_SET_PROJ_LIB" ]; then
    export PROJ_LIB=$_CONDA_SET_PROJ_LIB
    unset _CONDA_SET_PROJ_LIB
fi
