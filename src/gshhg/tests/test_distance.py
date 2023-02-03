import pickle

import pytest

from gshhg import Andoyer, Haversine, Spheroid, Thomas, Vincenty


def test_spheroid():
    spheroid = Spheroid()
    spheroid.a == pytest.approx(6378.137)
    spheroid.b == pytest.approx(6356.75231424517949756396)
    spheroid.f == pytest.approx(1 / 298.257223563)

    spheroid = Spheroid(1, 2)
    spheroid.a == pytest.approx(1)
    spheroid.b == pytest.approx(2)
    spheroid.f == pytest.approx(1)

    other = pickle.loads(pickle.dumps(spheroid))
    assert isinstance(other, Spheroid)


def test_adoyer():
    strategy = Andoyer()
    isinstance(strategy.model, Spheroid)
    other = pickle.loads(pickle.dumps(strategy))
    assert isinstance(other, Andoyer)


def test_haversine():
    strategy = Haversine()
    isinstance(strategy.model, Spheroid)
    other = pickle.loads(pickle.dumps(strategy))
    assert isinstance(other, Haversine)


def test_vincenty():
    strategy = Vincenty()
    isinstance(strategy.model, Spheroid)
    other = pickle.loads(pickle.dumps(strategy))
    assert isinstance(other, Vincenty)


def test_thomas():
    strategy = Thomas()
    isinstance(strategy.model, Thomas)
    other = pickle.loads(pickle.dumps(strategy))
    assert isinstance(other, Thomas)
