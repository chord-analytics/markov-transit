project(truncated_normal)
cmake_minimum_required(VERSION 2.8)
include(/usr/local/share/cmake/pybind11/pybind11Config.cmake)
pybind11_add_module(truncated_lognormal truncated_normal.cpp)