#----------------------------------------------------------------
# Generated CMake target import file for configuration "RELEASE".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "netCDF::netcdf" for configuration "RELEASE"
set_property(TARGET netCDF::netcdf APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(netCDF::netcdf PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libnetcdf.19.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libnetcdf.19.dylib"
  )

list(APPEND _IMPORT_CHECK_TARGETS netCDF::netcdf )
list(APPEND _IMPORT_CHECK_FILES_FOR_netCDF::netcdf "${_IMPORT_PREFIX}/lib/libnetcdf.19.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
