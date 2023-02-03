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

## Initialization.
The first step is to create an instance that will load the shorelines into memory.

```python
import gsshg

shorelines = gsshg("/Users/anonymous/Downloads/gshhg-shp-2.3.7/GSHHS_shp")
```

The constructor accepts the following options:
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

## Display

Once loaded in memory, it's possible to view the polygons loaded in memory. This
is useful for debugging possible problems with the handled data.

```python
instance.to_svg("intermediate.svg")
```

The created SVG file can be viewed in a browser. The resulting file for the
intermediate resolution is available [here](docs/intermediate.svg).

## Land/sea mask
For a set of coordinates expressed in degrees, it is possible to calculate the
value of the land/sea mask:

```python
import numpy


lon = np.random.uniform(-180.0, 180.0, 1000)
lat = np.random.uniform(-90.0, 90.0, 1000)
mask = instance(lon, lat, num_threads=0)
```

The variable `mask` contains values from 1 to 6 corresponding to different
hierarchical levels loaded or 0 if the data are located on ocean.

## Distance to the nearest shorelines

For a set of coordinates expressed in degrees, it is possible to calculate the
distance to the nearest coast point:

```python
distance = instance.distance_to_nearest(lon, lat, num_threads=0)
```

You can define a strategy to calculate distances in different ways between
points using the `strategy` option:
* [andoyer](https://www.boost.org/doc/libs/1_75_0/boost/geometry/strategies/geographic/distance_andoyer.hpp)
* [haversine](https://en.wikipedia.org/wiki/Haversine_formula)
* [thomas](https://www.boost.org/doc/libs/1_75_0/boost/geometry/strategies/geographic/distance_thomas.hpp)
* [vincenty](https://en.wikipedia.org/wiki/Vincenty%27s_formulae)

## Mapping land/sea mask

It's possible to create a grid representing the land/sea mask:

```python
ds = shorelines.grid_mapping_mask(step=0.25)
```

`ds` is a xarray dataset describing the mask created. The mask is a Dask array
that will have to be evaluated to be visualized, for example, or saved in a
netCDF file.

```python
ds.to_netcdf("/tmp/test.nc",
             encoding=dict(mask=dict(_FillValue=None)))
```
## Mapping distance to the nearest shorelines

It's possible to create a grid representing the land/sea mask:

```python
ds = instance.grid_mapping_distance_to_nearest(
    step=0.25,
    strategy="andoyer",
    num_threads=0)
```

`ds` is a xarray dataset describing the distance calculated. The distance is a Dask
array that will have to be evaluated to be visualized, for example, or saved in
a netCDF file.

```python
ds.to_netcdf("/tmp/test.nc",
             encoding=dict(distance=dict(_FillValue=None)))
```
