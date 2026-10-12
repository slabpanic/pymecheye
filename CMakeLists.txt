cmake_minimum_required(VERSION 3.18...3.30)
project(pymecheye LANGUAGES CXX)

if(NOT CMAKE_SYSTEM_NAME MATCHES "^(Linux|Windows)$"
   OR NOT CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64|amd64)$"
   OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
  message(FATAL_ERROR "MechEye requires Linux/Windows x86_64")
endif()
if(CMAKE_SYSTEM_NAME STREQUAL "Windows" AND NOT MSVC)
  message(FATAL_ERROR "MechEye on Windows requires the MSVC x64 C++ ABI")
endif()

find_package(Python 3.10 REQUIRED COMPONENTS Interpreter Development.Module)
execute_process(COMMAND "${Python_EXECUTABLE}" -c
  "import sys; sys.exit(0 if sys.implementation.name == 'cpython' else 'MechEye requires CPython')"
  RESULT_VARIABLE MECHEYE_PYTHON_CHECK)
if(NOT MECHEYE_PYTHON_CHECK EQUAL 0)
  message(FATAL_ERROR "MechEye requires CPython 3.10+")
endif()
find_package(nanobind CONFIG REQUIRED)
find_package(Threads REQUIRED)

include(cmake/MechEyeSdk.cmake)

# Use the regular ABI; nanobind enables free-threaded support only when the interpreter supports it.
nanobind_add_module(_native FREE_THREADED
  src/mecheye/native.cpp
  src/mecheye/bindings_values.cpp
  src/mecheye/bindings_arrays.cpp
  src/mecheye/bindings_frames.cpp
  src/mecheye/bindings_parameters.cpp
  src/mecheye/bindings_camera.cpp
  src/mecheye/bindings_descriptors.cpp
)
target_compile_features(_native PRIVATE cxx_std_17)
target_include_directories(_native SYSTEM PRIVATE "${MECHEYE_INCLUDE_DIR}")
target_link_libraries(_native PRIVATE "${MECHEYE_LIBRARY}" Threads::Threads)
set_target_properties(_native PROPERTIES INSTALL_RPATH "" INSTALL_RPATH_USE_LINK_PATH FALSE)
if(CMAKE_SYSTEM_NAME STREQUAL "Windows")
  # Match the vendor DLL's dynamic MSVC runtime and CRT ABI when passing STL objects across DLLs.
  target_compile_definitions(_native PRIVATE NOMINMAX)
  target_compile_options(_native PRIVATE /utf-8)
  set_property(TARGET _native PROPERTY MSVC_RUNTIME_LIBRARY MultiThreadedDLL)
endif()
option(MECHEYE_ENABLE_COVERAGE "Instrument the native binding for GCC coverage" OFF)
if(MECHEYE_ENABLE_COVERAGE)
  if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux" OR NOT CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    message(FATAL_ERROR "MECHEYE_ENABLE_COVERAGE requires GCC on Linux")
  endif()
  target_compile_options(_native PRIVATE --coverage -O0 -g -fprofile-update=atomic)
  target_link_options(_native PRIVATE --coverage)
endif()

install(TARGETS _native LIBRARY DESTINATION mecheye RUNTIME DESTINATION mecheye)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/runtime.json" DESTINATION mecheye/_runtime)
