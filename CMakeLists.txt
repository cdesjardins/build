cmake_minimum_required(VERSION 3.1)
project(cjd CXX)

set(CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../include")
include(compilerflags)

add_subdirectory (${CMAKE_CURRENT_SOURCE_DIR}/../CDLogger   ${CMAKE_CURRENT_BINARY_DIR}/CDLoggerBuild)
add_subdirectory (${CMAKE_CURRENT_SOURCE_DIR}/../cppssh     ${CMAKE_CURRENT_BINARY_DIR}/cppsshBuild)
add_subdirectory (${CMAKE_CURRENT_SOURCE_DIR}/../QueuePtr   ${CMAKE_CURRENT_BINARY_DIR}/QueuePtrBuild)
add_dependencies(cppssh botan)
add_custom_target(botan ${CMAKE_CURRENT_SOURCE_DIR}/../cppssh/buildbotan.sh)

