# Select the current platform's fixed default or an explicit environment override.
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
  set(MECHEYE_PLATFORM "linux")
  set(MECHEYE_DEFAULT_SDK_ROOT "/opt/mech-mind/mech-eye-sdk")
  set(MECHEYE_RUNTIME_RELATIVE "lib/libMechEyeApi.so")
  set(MECHEYE_LIBRARY_RELATIVE "${MECHEYE_RUNTIME_RELATIVE}")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Windows")
  set(MECHEYE_PLATFORM "win32")
  set(MECHEYE_DEFAULT_SDK_ROOT "C:/Mech-Mind/Mech-Eye SDK-2.6.0/API")
  set(MECHEYE_RUNTIME_RELATIVE "dll/MechEyeApi.dll")
  set(MECHEYE_LIBRARY_RELATIVE "lib/MechEyeApi.lib")
else()
  message(FATAL_ERROR "MechEye requires Linux/Windows x86_64")
endif()

if(DEFINED ENV{MECHEYE_SDK_ROOT} AND NOT "$ENV{MECHEYE_SDK_ROOT}" STREQUAL "")
  file(TO_CMAKE_PATH "$ENV{MECHEYE_SDK_ROOT}" MECHEYE_SDK_ROOT)
else()
  set(MECHEYE_SDK_ROOT "${MECHEYE_DEFAULT_SDK_ROOT}")
endif()
if(NOT IS_ABSOLUTE "${MECHEYE_SDK_ROOT}" OR NOT IS_DIRECTORY "${MECHEYE_SDK_ROOT}")
  message(FATAL_ERROR "MechEye SDK directory is invalid: ${MECHEYE_SDK_ROOT}. Set MECHEYE_SDK_ROOT to an existing absolute SDK directory")
endif()
get_filename_component(MECHEYE_SDK_ROOT "${MECHEYE_SDK_ROOT}" REALPATH)

# The shared validator checks the SDK files and binary platform, then records
# runtime identity without storing a machine-specific SDK path in the wheel.
execute_process(
  COMMAND "${Python_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/src/mecheye/_sdk.py"
    --manifest "${CMAKE_CURRENT_BINARY_DIR}/runtime.json"
    --soabi "${Python_SOABI}" --platform "${MECHEYE_PLATFORM}"
  RESULT_VARIABLE MECHEYE_SDK_CHECK
  ERROR_VARIABLE MECHEYE_SDK_ERROR)
if(NOT MECHEYE_SDK_CHECK EQUAL 0)
  message(FATAL_ERROR "Invalid Mech-Eye C++ SDK: ${MECHEYE_SDK_ERROR}")
endif()
set(MECHEYE_INCLUDE_DIR "${MECHEYE_SDK_ROOT}/include")
set(MECHEYE_LIBRARY "${MECHEYE_SDK_ROOT}/${MECHEYE_LIBRARY_RELATIVE}")
message(STATUS "Using external Mech-Eye SDK: ${MECHEYE_SDK_ROOT}")
