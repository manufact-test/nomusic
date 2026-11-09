cmake_minimum_required(VERSION 3.18.1)
project(celikom_host_probe LANGUAGES C)
add_library(celikom_host_probe SHARED native_probe.c)
