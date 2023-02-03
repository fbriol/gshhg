from typing import List, Optional, Tuple, overload

import numpy

class Andoyer:

    def __init__(self, wgs: Optional[Spheroid] = ...) -> None:
        ...

    @property
    def model(self) -> Spheroid:
        ...


class GSHHG:

    def __init__(
            self,
            dirname: str,
            resolution: Optional[str] = ...,
            levels: Optional[List[int]] = ...,
            bbox: Optional[Tuple[float, float, float, float]] = ...) -> None:
        ...

    @overload
    def distance_to_nearest(
            self,
            lon: numpy.ndarray[numpy.float64],
            lat: numpy.ndarray[numpy.float64],
            strategy: Optional[Andoyer] = ...,
            num_threads: int = ...) -> numpy.ndarray[numpy.float64]:
        ...

    @overload
    def distance_to_nearest(
            self,
            lon: numpy.ndarray[numpy.float64],
            lat: numpy.ndarray[numpy.float64],
            strategy: Optional[Haversine],
            num_threads: int = ...) -> numpy.ndarray[numpy.float64]:
        ...

    @overload
    def distance_to_nearest(
            self,
            lon: numpy.ndarray[numpy.float64],
            lat: numpy.ndarray[numpy.float64],
            strategy: Optional[Thomas],
            num_threads: int = ...) -> numpy.ndarray[numpy.float64]:
        ...

    @overload
    def distance_to_nearest(
            self,
            lon: numpy.ndarray[numpy.float64],
            lat: numpy.ndarray[numpy.float64],
            strategy: Optional[Vincenty],
            num_threads: int = ...) -> numpy.ndarray[numpy.float64]:
        ...

    def mask(self,
             lon: numpy.ndarray[numpy.float64],
             lat: numpy.ndarray[numpy.float64],
             num_threads: int = ...) -> numpy.ndarray[numpy.int8]:
        ...

    def nearest(self,
                lon: numpy.ndarray[numpy.float64],
                lat: numpy.ndarray[numpy.float64],
                num_threads: int = ...) -> tuple:
        ...

    def points(self) -> int:
        ...

    def polygons(self) -> int:
        ...

    def to_svg(self,
               filename: str,
               width: int = ...,
               height: int = ...) -> None:
        ...


class Haversine:

    def __init__(self, wgs: Optional[Spheroid] = ...) -> None:
        ...

    @property
    def model(self) -> Spheroid:
        ...


class Spheroid:

    @overload
    def __init__(self) -> None:
        ...

    @overload
    def __init__(self, a: float, b: float) -> None:
        ...

    @property
    def a(self) -> float:
        ...

    @property
    def b(self) -> float:
        ...

    @property
    def f(self) -> float:
        ...


class Thomas:

    def __init__(self, wgs: Optional[Spheroid] = ...) -> None:
        ...

    @property
    def model(self) -> Spheroid:
        ...


class Vincenty:

    def __init__(self, wgs: Optional[Spheroid] = ...) -> None:
        ...

    @property
    def model(self) -> Spheroid:
        ...
