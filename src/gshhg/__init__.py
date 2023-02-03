from __future__ import annotations

import collections
import pathlib
from typing import Any, Callable

import dask.array
import dask.array.core
import numpy
import xarray

from . import core


def _normalize_longitude(lon: float) -> float:
    """Normalize longitudes between [-180, 180]"""
    return ((lon + 180.0) % 360.0) - 180.0


class Spheroid(core.Spheroid):
    """Spheroid model."""

    def __reduce__(self) -> str | tuple[Any, ...]:
        return Spheroid, (self.a, self.b)


class Andoyer(core.Andoyer):
    """Andoyer's formulae for geodesics on an ellipsoid."""

    def __reduce__(self) -> str | tuple[Any, ...]:
        model = self.model
        return Andoyer, (Spheroid(model.a, model.b), )


class Haversine(core.Haversine):
    """Haversine formulae for geodesics on an ellipsoid."""

    def __reduce__(self) -> str | tuple[Any, ...]:
        model = self.model
        return Haversine, (Spheroid(model.a, model.b), )


class Thomas(core.Thomas):
    """Thomas' formulae for geodesics on an ellipsoid."""

    def __reduce__(self) -> str | tuple[Any, ...]:
        model = self.model
        return Thomas, (Spheroid(model.a, model.b), )


class Vincenty(core.Vincenty):
    """Vincenty's formulae for geodesics on an ellipsoid."""

    def __reduce__(self) -> str | tuple[Any, ...]:
        model = self.model
        return Vincenty, (Spheroid(model.a, model.b), )


def _grid_mapping_mask(lon: numpy.ndarray,
                       lat: numpy.ndarray,
                       dirname: str | pathlib.Path,
                       resolution: str | None,
                       levels: list[int] | None,
                       bbox: tuple[float, float, float, float],
                       kwargs=None) -> numpy.ndarray:
    kwargs = kwargs or dict()
    instance = core.GSHHG(str(dirname), resolution, levels, bbox=bbox)
    mx, my = numpy.meshgrid(lon, lat)
    return instance.mask(mx.flatten(), my.flatten(),
                         **kwargs).reshape(mx.shape)


def _grid_mapping_distance_to_nearest(lon: numpy.ndarray,
                                      lat: numpy.ndarray,
                                      dirname: str | pathlib.Path,
                                      resolution: str | None,
                                      levels: list[int] | None,
                                      bbox: tuple[float, float, float, float],
                                      kwargs=None) -> numpy.ndarray:
    kwargs = kwargs or dict()
    instance = core.GSHHG(str(dirname), resolution, levels, bbox=bbox)
    mx, my = numpy.meshgrid(lon, lat)
    return instance.distance_to_nearest(mx.flatten(), my.flatten(),
                                        **kwargs).reshape(mx.shape)


class GSHHG(core.GSHHG):
    __slots__ = ('dirname', 'resolution', 'levels', 'bbox')

    def __init__(
            self,
            dirname: str | pathlib.Path,
            resolution: str | None = None,
            levels: list[int] | None = None,
            bbox: tuple[float, float, float, float] | None = None) -> None:
        if isinstance(dirname, str):
            dirname = pathlib.Path(dirname)
        if not dirname.exists():
            raise FileNotFoundError(f'no such file or directory: {dirname}')
        if not dirname.is_dir():
            raise ValueError(f'not a directory: {dirname}')
        if levels is not None and (min(levels) < 1 or max(levels) > 6):
            raise ValueError('values of the levels must be within [1, 6]')
        if bbox is not None:
            bbox = (_normalize_longitude(bbox[0]), bbox[1],
                    _normalize_longitude(bbox[2]), bbox[3])

        super().__init__(str(dirname), resolution, levels, bbox)

        (self.dirname, self.resolution, self.levels,
         self.bbox) = (dirname, resolution, levels, bbox)

    def to_svg(self,
               filename: str | pathlib.Path,
               width: int = 1200,
               height: int = 600) -> None:
        return super().to_svg(
            str(filename) if isinstance(filename, pathlib.Path) else filename,
            width, height)

    def distance_to_nearest(  # type: ignore[override]
        self,
        lon: numpy.ndarray,
        lat: numpy.ndarray,
        strategy: str | None = None,
        num_threads: int = 0,
    ) -> numpy.ndarray:
        return super().distance_to_nearest(lon,
                                           lat,
                                           strategy=self._get_strategy(
                                               strategy or 'vincenty'),
                                           num_threads=num_threads)

    def __reduce__(self) -> tuple[Any, ...]:
        return GSHHG, (self.dirname, self.resolution, self.levels, self.bbox)

    @staticmethod
    def _dataset_template(
        lon: numpy.ndarray, lat: numpy.ndarray
    ) -> tuple[collections.OrderedDict, xarray.DataArray]:
        coords = collections.OrderedDict(lon=xarray.DataArray(
            lon,
            dims=('lon', ),
            coords=dict(lon=lon),
            attrs=collections.OrderedDict(axis='X',
                                          long_name='longitude',
                                          standard_name='longitude',
                                          unit_long='degrees east',
                                          units='degrees_east')),
                                         lat=xarray.DataArray(
                                             lat,
                                             dims=('lat', ),
                                             coords=dict(lat=lat),
                                             attrs=collections.OrderedDict(
                                                 axis='Y',
                                                 long_name='latitude',
                                                 standard_name='latitude',
                                                 unit_long='degrees north',
                                                 units='degrees_north')))

        crs = xarray.DataArray(
            numpy.int32(0),
            dims=(),
            attrs=collections.OrderedDict(
                comment='This is a container variable that describes the '
                'grid_mapping used by the data in this file. This variable '
                'does not contain any data; only information about the '
                'geographic coordinate system.',
                inverse_flattening=298.257223563,
                semi_major_axis=6378137.0,
                grid_mapping_name='latitude_longitude',
                epsg_code='EPSG:4326',
            ))
        return coords, crs

    def _lon_lat_arange(self,
                        step: float) -> tuple[numpy.ndarray, numpy.ndarray]:
        if self.bbox is not None:
            return numpy.arange(self.bbox[0],
                                self.bbox[2] + step,
                                step,
                                dtype='float64'), numpy.arange(self.bbox[1],
                                                               self.bbox[3] +
                                                               step,
                                                               step,
                                                               dtype='float64')
        return numpy.arange(-180, 180, step,
                            dtype='float64'), numpy.arange(-90,
                                                           90 + step,
                                                           step,
                                                           dtype='float64')

    def _dask_array(
            self,
            function: Callable,
            dtype: numpy.dtype,
            name: str,
            step: float,
            blocksize: int | None = None,
            **kwargs) -> tuple[numpy.ndarray, numpy.ndarray, dask.array.Array]:
        lon, lat = self._lon_lat_arange(step)
        nx, ny = len(lon), len(lat)

        if blocksize is None:
            chunks = dask.array.core.normalize_chunks(chunks='auto',
                                                      shape=(ny, nx),
                                                      limit=90 * 90 *
                                                      dtype.itemsize,
                                                      dtype=dtype)
        else:
            chunks = [(blocksize, ) * (ny // blocksize),
                      (blocksize, ) * (nx // blocksize)]
            samples = sum(chunks[0])
            if samples != ny:
                chunks[0] = chunks[0] + (ny - samples, )
            samples = sum(chunks[1])
            if samples != nx:
                chunks[1] = chunks[1] + (nx - samples, )

        ychunks, xchunks = chunks

        dsk = {}
        for iy in range(len(ychunks)):
            y_slice = lat[sum(ychunks[0:iy]):sum(ychunks[0:iy + 1])]
            y_max = max(y_slice[-1] + step, lat[-1])
            y_min = min(y_slice[0] - step, lat[0])

            for ix in range(len(xchunks)):
                x_slice = lon[sum(xchunks[0:ix]):sum(xchunks[0:ix + 1])]
                x_max = max(x_slice[-1] + step, lon[-1])
                x_min = min(x_slice[0] - step, lon[0])

                dsk[(name, iy, ix)] = (function, x_slice, y_slice,
                                       str(self.dirname), self.resolution,
                                       self.levels, (x_min, y_min, x_max,
                                                     y_max), kwargs)

        return lon, lat, dask.array.Array(dsk, name, chunks, dtype)

    def grid_mapping_mask(self,
                          step: float,
                          blocksize: int | None = None,
                          num_threads: int = 1) -> xarray.Dataset:
        lon, lat, array = self._dask_array(_grid_mapping_mask,
                                           numpy.dtype('int8'),
                                           'grid_mapping_mask',
                                           step,
                                           blocksize,
                                           num_threads=num_threads)
        coords, crs = self._dataset_template(lon, lat)
        data_vars = collections.OrderedDict(
            crs=crs,
            mask=xarray.DataArray(
                array,
                dims=('lat', 'lon'),
                attrs=collections.OrderedDict(
                    cell_methods='lat: point lon: point',
                    coordinates='lat lon',
                    flag_meanings='ocean land lake island-in-lake '
                    'pond-in-island antartica-ice antartica-land',
                    flag_values=numpy.arange(0, 7, dtype=numpy.uint8),
                    long_name='land sea mask',
                    valid_range=numpy.array([0, 6], dtype=numpy.uint8))))

        return xarray.Dataset(data_vars=data_vars, coords=coords)

    @staticmethod
    def _get_strategy(strategy: str) -> Any:
        if strategy == 'andoyer':
            return Andoyer()
        if strategy == 'haversine':
            return Haversine()
        if strategy == 'thomas':
            return Thomas()
        if strategy == 'vincenty':
            return Vincenty()
        raise ValueError('unknown strategy: ' + repr(strategy))

    def grid_mapping_distance_to_nearest(
            self,
            step: float,
            strategy: str | None = None,
            num_threads: int = 0) -> xarray.Dataset:
        strategy = strategy or 'vincenty'

        lon, lat, array = self._dask_array(
            _grid_mapping_distance_to_nearest,
            numpy.dtype('float64'),
            'grid_mapping_distance_to_nearest',
            step,
            # Here it's not possible to run the calculation in different
            # tasks.
            blocksize=2**64 - 1,
            num_threads=num_threads,
            strategy=self._get_strategy(strategy))
        coords, crs = self._dataset_template(lon, lat)
        data_vars = collections.OrderedDict(
            crs=crs,
            distance=xarray.DataArray(
                array * 1e-3,
                dims=('lat', 'lon'),
                attrs=collections.OrderedDict(
                    cell_methods='lat: point lon: point',
                    coordinates='lat lon',
                    long_name='distance to the nearest coastline',
                    units='km')))

        return xarray.Dataset(data_vars=data_vars, coords=coords)
