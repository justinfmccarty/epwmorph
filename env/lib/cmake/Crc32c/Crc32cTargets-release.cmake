#----------------------------------------------------------------
# Generated CMake target import file for configuration "release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "Crc32c::crc32c" for configuration "release"
set_property(TARGET Crc32c::crc32c APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Crc32c::crc32c PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libcrc32c.1.1.0.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libcrc32c.1.dylib"
  )

list(APPEND _IMPORT_CHECK_TARGETS Crc32c::crc32c )
list(APPEND _IMPORT_CHECK_FILES_FOR_Crc32c::crc32c "${_IMPORT_PREFIX}/lib/libcrc32c.1.1.0.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
