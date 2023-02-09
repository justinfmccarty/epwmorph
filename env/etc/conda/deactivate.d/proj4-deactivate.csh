#!/usr/bin/env csh

# Restore previous env vars if they were set.
unsetenv PROJ_LIB
unsetenv PROJ_NETWORK

if ( $?_CONDA_SET_PROJ_LIB ) then
    setenv PROJ_LIB "$_CONDA_SET_PROJ_LIB"
    unsetenv _CONDA_SET_PROJ_LIB
endif
