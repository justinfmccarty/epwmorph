#!/usr/bin/env fish

# Restore previous env vars if they were set.
set -e PROJ_LIB
set -e PROJ_NETWORK

if set -q _CONDA_SET_PROJ_LIB
    set -gx  PROJ_LIB "$_CONDA_SET_PROJ_LIB"
    set -e _CONDA_SET_PROJ_LIB
end
