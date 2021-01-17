# gshhg
Handle calculations from GSHHG shorelines

# Description

Small tool that automatically calculates the following metrics from GSHHG coastlines:
* land/sea mask,
* distance to the nearest coastline from a point.

# Installation

## Requirements

Because of the programs written in Python, and some parts of the library in C++, you must have Python 3, at least Python version 3.6, a C++ compiler and cmake installed on your system to build the library.

> The C++ compiler must support the ISO C++ 2017 standard

The compiling C++ requires the following development library:
* [Boost C++ libraries](https://www.boost.org/)
* [cmake](https://cmake.org/)
* [pybind11](https://github.com/pybind/pybind11)
* [Shapelib](http://shapelib.maptools.org/)

You need, also, to install Python libraries before configuring and installing this software:
* [dask](https://dask.org/)
* [numpy](https://numpy.org/)
* [xarray](http://xarray.pydata.org/)

You can install these packages with [conda](https://docs.conda.io/en/latest/) by typing the following command:

    conda install -c conda-forge dask boost-cpp cmake pybind11 shapelib xarray

## Build

Once you have satisfied the requirements detailed above, to build the library, type the command `python3 setup.py build` at the root of the project.

You can specify, among other things, the following options:
* --boost-root to specify the Preferred Boost installation prefix.
* --cxx-compiler to select the C++ compiler to use.
* --reconfigure to force CMake to reconfigure the project.

Run the `python3 setup.py build --help command` to view all the options available for building the library.

## Test

### Requirements

Running tests require the following Python libraries:
* [pytest](https://docs.pytest.org)

### Running tests
The distribution contains a set of test cases that can be processed with `pytest`. To run the full test suite, use the following at the root of the project:

    pytest

## Install

To install this library, type the command `python3 setup.py install`. You can specify an alternate installation path, with:

    python setup.py install --prefix=/opt/local

# Usage

The software uses GSHHG shorelines to perform the calculations. You must download these files to use the library here : https://www.ngdc.noaa.gov/mgg/shorelines/data/gshhg/latest/

> This library has been tested with GSHHG data version 2.3.7.

The first step is to create an instance that will load the shorelines into memory.

    import gsshg

    shorelines = gsshg("/Users/anonymous/Downloads/gshhg-shp-2.3.7/GSHHS_shp", resolution="full")

The contructor accepts the following options:    
* `resolution`, specifies the geographic resolution to use:
  * `crude`
  * `low`
  * `intermediate` (default value)
  * `high`
  * `full`
* `levels`, a list of integers, which can contain values from 1 to 6, 
  specifying the hierarchical levels to be loaded:
  * 1: boundary between land and ocean, except Antarctica.
  * 2: boundary between lake and land.
  * 3: boundary between island-in-lake and lake.
  * 4: boundary between pond-in-island and island.
  * 5: boundary between Antarctica ice and ocean.
  * 6: boundary between Antarctica grounding-line and ocean.
  
  If `levels` is not set, all levels are loaded.

* `bbox`, a tuple of 4 floats (minimum longitude, minimum latitude, maximum
  longitude, and maximum latitude) defines the geographical area to be
  processed. By default, the whole data read.