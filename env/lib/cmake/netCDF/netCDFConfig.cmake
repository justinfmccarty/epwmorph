# NetCDF Configuration Summary
#
# General
#

####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was netCDFConfig.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../../../" ABSOLUTE)

macro(set_and_check _var _file)
  set(${_var} "${_file}")
  if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
  endif()
endmacro()

####################################################################################

set(NetCDFVersion "4.8.1")
set_and_check(netCDF_INSTALL_PREFIX "${PACKAGE_PREFIX_DIR}")
set_and_check(netCDF_INCLUDE_DIR "${PACKAGE_PREFIX_DIR}/include")
set_and_check(netCDF_LIB_DIR "${PACKAGE_PREFIX_DIR}/lib")

set(netCDF_LIBRARIES netCDF::netcdf)

# include target information
include("${CMAKE_CURRENT_LIST_DIR}/netCDFTargets.cmake")

# Compiling Options
#
set(netCDF_C_COMPILER "/Users/runner/miniforge3/conda-bld/libnetcdf_1630368161103/_build_env/bin/arm64-apple-darwin20.0.0-clang")
set(netCDF_C_COMPILER_FLAGS "-ftree-vectorize -fPIC -fPIE -fstack-protector-strong -O2 -pipe -isystem /Users/jmccarty/GitHub/epwmorph/env/include -fdebug-prefix-map=/Users/runner/miniforge3/conda-bld/libnetcdf_1630368161103/work=/usr/local/src/conda/libnetcdf-4.8.1 -fdebug-prefix-map=/Users/jmccarty/GitHub/epwmorph/env=/usr/local/src/conda-prefix -fno-strict-aliasing -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64 -O3 -DNDEBUG")
set(netCDF_C_CPP_FLAGS " ")
set(netCDF_LDFLAGS "-Wl,-pie -Wl,-headerpad_max_install_names  -Wl,-rpath,/Users/jmccarty/GitHub/epwmorph/env/lib -L/Users/jmccarty/GitHub/epwmorph/env/lib ")
set(netCDF_AM_CFLAGS "")
set(netCDF_AM_CPPFLAGS "")
set(netCDF_AM_LDFLAGS "")
set(netCDF_SHARED yes)
set(netCDF_STATIC no)

# Features:
#
set(netCDF_HAS_NC2 yes)
set(netCDF_HAS_NC4 yes)
set(netCDF_HAS_HDF4 yes)
set(netCDF_HAS_HDF5 yes)
set(netCDF_HAS_PNETCDF no)
set(netCDF_HAS_PARALLEL no)
set(netCDF_HAS_DAP yes)
set(netCDF_HAS_DAP2 yes)
set(netCDF_HAS_DAP4 yes)
set(netCDF_HAS_DISKLESS yes)
set(netCDF_HAS_MMAP yes)
set(netCDF_HAS_JNA no)
