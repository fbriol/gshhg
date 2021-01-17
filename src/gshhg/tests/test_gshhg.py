import pathlib
import pickle
import numpy as np
import pytest
try:
    import matplotlib.pyplot
    HAVE_PLT = True
except ImportError:
    HAVE_PLT = False
import gshhg


def get_dirname() -> pathlib.Path:
    return pathlib.Path(__file__).absolute().parent.joinpath('GSHHS_shp')


def test_construct():
    instance = gshhg.GSHHG(get_dirname(), resolution="crude")
    assert instance.polygons() != 0
    assert instance.points() != 0

    instance = gshhg.GSHHG(get_dirname(),
                           resolution="crude",
                           levels=[6],
                           bbox=(-10, -20, 10, 20))
    assert instance.dirname == get_dirname()
    assert instance.resolution == "crude"
    assert instance.levels == [6]
    assert instance.bbox == (-10, -20, 10, 20)

    other = pickle.loads(pickle.dumps(instance))
    assert other.polygons() == instance.polygons()
    assert other.points() == instance.points()

    with pytest.raises(FileNotFoundError):
        gshhg.GSHHG(get_dirname().parent, resolution="crude")

    with pytest.raises(ValueError):
        gshhg.GSHHG(get_dirname(), resolution="CRUDE")

    with pytest.raises(ValueError):
        gshhg.GSHHG(get_dirname(), levels=[0])

    with pytest.raises(ValueError):
        gshhg.GSHHG(get_dirname(), levels=[7])

    with pytest.raises(IndexError):
        gshhg.GSHHG(get_dirname(), bbox=(0, ))


def get_figure_path(path: str) -> pathlib.Path:
    dirname = pathlib.Path(__file__).absolute().parent.joinpath("figures")
    dirname.mkdir(exist_ok=True, parents=True)
    return dirname.joinpath(path)


def test_to_svg():
    instance = gshhg.GSHHG(get_dirname(), resolution="crude")
    figure = get_figure_path("crude.svg")
    if figure.exists():
        figure.unlink()
    assert not figure.exists()
    instance.to_svg(figure)
    assert figure.exists()


def test_nearest():
    instance = gshhg.GSHHG(get_dirname(), resolution="crude")
    lon1 = np.random.uniform(-180.0, 180.0, 1000)
    lat1 = np.random.uniform(-90.0, 90.0, 1000)

    lon2, lat2 = instance.nearest(lon1, lat1, num_threads=0)
    lon3, lat3 = instance.nearest(lon1, lat1, num_threads=1)

    assert np.any(lon1 != lon2)
    assert np.any(lat1 != lat2)
    assert np.all(lon2 == lon3)
    assert np.all(lat2 == lat3)


def test_distance_to_nearest():
    instance = gshhg.GSHHG(get_dirname(), resolution="crude")
    lon = np.random.uniform(-180.0, 180.0, 1000)
    lat = np.random.uniform(-90.0, 90.0, 1000)

    d1 = instance.distance_to_nearest(lon, lat, num_threads=0)
    d2 = instance.distance_to_nearest(lon, lat, num_threads=1)

    assert np.all(d1 == d2)

    d1 = instance.distance_to_nearest(lon, lat, strategy=gshhg.Andoyer())
    d2 = instance.distance_to_nearest(lon, lat, strategy=gshhg.Haversine())
    d3 = instance.distance_to_nearest(lon, lat, strategy=gshhg.Thomas())
    d4 = instance.distance_to_nearest(lon, lat, strategy=gshhg.Vincenty())

    assert np.all(d1 != d2)
    assert np.all(d1 != d3)
    assert np.all(d1 != d4)
    assert np.all(d2 != d3)
    assert np.all(d2 != d4)
    assert np.all(d3 != d4)


def test_mask():
    instance = gshhg.GSHHG(get_dirname(), resolution="crude")

    lon = np.arange(-180, 180, 1, dtype=np.float64)
    lat = np.arange(-90, 90, 1, dtype=np.float64)
    mx, my = np.meshgrid(lon, lat)

    mask1 = instance.mask(mx.flatten(), my.flatten(), num_threads=0)
    mask2 = instance.mask(mx.flatten(), my.flatten(), num_threads=1)

    assert np.all(mask1 == mask2)
    assert set(mask1) == set((0, 1, 2, 3, 5, 6))


def test_grid_mapping_mask():
    instance = gshhg.GSHHG(get_dirname(), resolution="crude")
    ds = instance.grid_mapping_mask(0.25)
    array = ds.mask.data.compute()
    assert set(array.flatten()) == set((0, 1, 2, 3, 5, 6))
    if HAVE_PLT:
        figure = matplotlib.pyplot.figure(figsize=(15, 15), dpi=150)
        axe = figure.add_subplot(2, 1, 1)
        mx, my = np.meshgrid(ds.lon, ds.lat)
        axe.pcolormesh(mx, my, ds.mask, shading='auto')
        figure.savefig(get_figure_path("mask.png"),
                       bbox_inches='tight',
                       pad_inches=0.4)


def test_grid_mapping_distance_to_nearest():
    instance = gshhg.GSHHG(get_dirname(), resolution="crude")
    ds = instance.grid_mapping_distance_to_nearest(0.25)
    array = ds.distance.data.compute()
    assert array.mean() != 0
    if HAVE_PLT:
        figure = matplotlib.pyplot.figure(figsize=(15, 15), dpi=150)
        axe = figure.add_subplot(2, 1, 1)
        mx, my = np.meshgrid(ds.lon, ds.lat)
        axe.pcolormesh(mx, my, ds.distance, shading='auto')
        figure.savefig(get_figure_path("distance_to_nearest.png"),
                       bbox_inches='tight',
                       pad_inches=0.4)
