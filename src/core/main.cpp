#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "broadcast.hpp"
#include "gshhg.hpp"
#include "thread.hpp"

namespace py = pybind11;

namespace gshhg {
py::tuple nearest(const GSHHG& self, const py::array_t<double>& lon,
                  const py::array_t<double>& lat, const size_t num_threads) {
  check_array_ndim("lon", 1, lon, "lat", 1, lat);
  check_container_size("lon", lon, "lat", lat);

  auto size = lon.size();
  auto x = py::array_t<double>(py::array::ShapeContainer{size});
  auto y = py::array_t<double>(py::array::ShapeContainer{size});

  auto _lon = lon.template unchecked<1>();
  auto _lat = lat.template unchecked<1>();
  auto _x = x.template mutable_unchecked<1>();
  auto _y = y.template mutable_unchecked<1>();

  {
    // Captures the detected exceptions in the calculation function
    // (only the last exception captured is kept)
    auto except = std::exception_ptr(nullptr);

    py::gil_scoped_release release;

    dispatch(
        [&](const size_t start, const size_t end) {
          try {
            for (size_t ix = start; ix < end; ++ix) {
              auto point = self.nearest(_lon(ix), _lat(ix));
              _x(ix) = point.get<0>();
              _y(ix) = point.get<1>();
            }
          } catch (...) {
            except = std::current_exception();
          }
        },
        size, num_threads);
    if (except != nullptr) {
      std::rethrow_exception(except);
    }
  }
  return py::make_tuple(x, y);
}

py::array_t<int8_t> mask(const GSHHG& self, const py::array_t<double>& lon,
                         const py::array_t<double>& lat,
                         const size_t num_threads) {
  check_array_ndim("lon", 1, lon, "lat", 1, lat);
  check_container_size("lon", lon, "lat", lat);

  auto size = lon.size();
  auto mask = py::array_t<int8_t>(py::array::ShapeContainer{size});

  auto _lon = lon.unchecked<1>();
  auto _lat = lat.unchecked<1>();
  auto _mask = mask.mutable_unchecked<1>();

  {
    // Captures the detected exceptions in the calculation function
    // (only the last exception captured is kept)
    auto except = std::exception_ptr(nullptr);

    py::gil_scoped_release release;

    dispatch(
        [&](const size_t start, const size_t end) {
          try {
            for (size_t ix = start; ix < end; ++ix) {
              _mask(ix) = self.mask(_lon(ix), _lat(ix));
            }
          } catch (...) {
            except = std::current_exception();
          }
        },
        size, num_threads);
    if (except != nullptr) {
      std::rethrow_exception(except);
    }
  }
  return mask;
}

template <class Strategy>
py::array_t<double> distance_to_nearest(const GSHHG& self,
                                        const py::array_t<double>& lon,
                                        const py::array_t<double>& lat,
                                        const Strategy& strategy,
                                        const size_t num_threads) {
  check_array_ndim("lon", 1, lon, "lat", 1, lat);
  check_container_size("lon", lon, "lat", lat);

  auto size = lon.size();
  auto result = py::array_t<double>(py::array::ShapeContainer{size});

  auto _lon = lon.unchecked<1>();
  auto _lat = lat.unchecked<1>();
  auto _result = result.mutable_unchecked<1>();

  {
    // Captures the detected exceptions in the calculation function
    // (only the last exception captured is kept)
    auto except = std::exception_ptr(nullptr);

    py::gil_scoped_release release;

    dispatch(
        [&](const size_t start, const size_t end) {
          try {
            for (size_t ix = start; ix < end; ++ix) {
              _result(ix) =
                  self.distance_to_nearest(_lon(ix), _lat(ix), strategy);
            }
          } catch (...) {
            except = std::current_exception();
          }
        },
        size, num_threads);
    if (except != nullptr) {
      std::rethrow_exception(except);
    }
  }
  return result;
}

}  // namespace gshhg

PYBIND11_MODULE(core, m) {
  py::register_exception_translator([](std::exception_ptr p) {
    try {
      if (p) std::rethrow_exception(p);
    } catch (const std::system_error& e) {
      if (e.code().value() == ENOENT) {
        PyErr_SetString(PyExc_FileNotFoundError, e.code().message().c_str());
      } else {
        PyErr_SetString(PyExc_OSError, e.code().message().c_str());
      }
    }
  });

  py::class_<gshhg::Spheroid>(m, "Spheroid")
      .def(py::init<>())
      .def(py::init<double, double>(), py::arg("a"), py::arg("b"))
      .def_property_readonly("a",
                             [](const gshhg::Spheroid& self) -> double {
                               return self.get_radius<1>();
                             })
      .def_property_readonly("b",
                             [](const gshhg::Spheroid& self) -> double {
                               return self.get_radius<2>();
                             })
      .def_property_readonly("f", [](const gshhg::Spheroid& self) -> double {
        return (self.get_radius<1>() - self.get_radius<2>()) /
               self.get_radius<1>();
      });

  py::class_<gshhg::Andoyer>(m, "Andoyer")
      .def(py::init([](const std::optional<gshhg::Spheroid>& spheroid) {
             return std::make_unique<gshhg::Andoyer>(
                 spheroid.value_or(gshhg::Spheroid()));
           }),
           py::arg("wgs") = py::none())
      .def_property_readonly("model",
                             [](const gshhg::Andoyer& self) -> gshhg::Spheroid {
                               return self.model();
                             });

  py::class_<gshhg::Haversine>(m, "Haversine")
      .def(py::init([](const std::optional<gshhg::Spheroid>& spheroid) {
             return std::make_unique<gshhg::Haversine>(
                 spheroid.value_or(gshhg::Spheroid()));
           }),
           py::arg("wgs") = py::none())
      .def_property_readonly(
          "model", [](const gshhg::Haversine& self) -> gshhg::Spheroid {
            return gshhg::Spheroid(self.radius(), self.radius());
          });

  py::class_<gshhg::Thomas>(m, "Thomas")
      .def(py::init([](const std::optional<gshhg::Spheroid>& spheroid) {
             return std::make_unique<gshhg::Thomas>(
                 spheroid.value_or(gshhg::Spheroid()));
           }),
           py::arg("wgs") = py::none())
      .def_property_readonly("model",
                             [](const gshhg::Thomas& self) -> gshhg::Spheroid {
                               return self.model();
                             });

  py::class_<gshhg::Vincenty>(m, "Vincenty")
      .def(py::init([](const std::optional<gshhg::Spheroid>& spheroid) {
             return std::make_unique<gshhg::Vincenty>(
                 spheroid.value_or(gshhg::Spheroid()));
           }),
           py::arg("wgs") = py::none())
      .def_property_readonly(
          "model", [](const gshhg::Vincenty& self) -> gshhg::Spheroid {
            return self.model();
          });

  py::class_<gshhg::GSHHG>(m, "GSHHG")
      .def(py::init([](const std::string& filename,
                       const std::optional<std::string>& resolution,
                       const std::optional<std::vector<int>>& levels,
                       const std::optional<
                           std::tuple<double, double, double, double>>& bbox) {
             auto box =
                 bbox.has_value()
                     ? std::make_optional<gshhg::Box>(
                           gshhg::Point{std::get<0>(*bbox), std::get<1>(*bbox)},
                           gshhg::Point{std::get<2>(*bbox), std::get<3>(*bbox)})
                     : std::optional<gshhg::Box>();
             return std::make_unique<gshhg::GSHHG>(filename, resolution, levels,
                                                   box);
           }),
           py::arg("dirname"), py::arg("resolution") = py::none(),
           py::arg("levels") = py::none(), py::arg("bbox") = py::none(),
           py::call_guard<py::gil_scoped_release>())
      .def("points", &gshhg::GSHHG::points)
      .def("polygons", &gshhg::GSHHG::polygons)
      .def("to_svg", &gshhg::GSHHG::to_svg, py::arg("filename"),
           py::arg("width") = 1200, py::arg("height") = 600,
           py::call_guard<py::gil_scoped_release>())
      .def(
          "nearest",
          [](const gshhg::GSHHG& self, const py::array_t<double>& lon,
             const py::array_t<double>& lat,
             const size_t num_threads) -> py::tuple {
            return gshhg::nearest(self, lon, lat, num_threads);
          },
          py::arg("lon"), py::arg("lat"), py::arg("num_threads") = 0)
      .def(
          "distance_to_nearest",
          [](const gshhg::GSHHG& self, const py::array_t<double>& lon,
             const py::array_t<double>& lat,
             const std::optional<gshhg::Andoyer>& strategy,
             const size_t num_threads) -> py::array_t<double> {
            return gshhg::distance_to_nearest(
                self, lon, lat, strategy.value_or(gshhg::Andoyer()),
                num_threads);
          },
          py::arg("lon"), py::arg("lat"), py::arg("strategy") = py::none(),
          py::arg("num_threads") = 0)
      .def(
          "distance_to_nearest",
          [](const gshhg::GSHHG& self, const py::array_t<double>& lon,
             const py::array_t<double>& lat,
             const std::optional<gshhg::Haversine>& strategy,
             const size_t num_threads) -> py::array_t<double> {
            return gshhg::distance_to_nearest(
                self, lon, lat, strategy.value_or(gshhg::Haversine()),
                num_threads);
          },
          py::arg("lon"), py::arg("lat"), py::arg("strategy"),
          py::arg("num_threads") = 0)
      .def(
          "distance_to_nearest",
          [](const gshhg::GSHHG& self, const py::array_t<double>& lon,
             const py::array_t<double>& lat,
             std::optional<gshhg::Thomas>& strategy,
             const size_t num_threads) -> py::array_t<double> {
            return gshhg::distance_to_nearest(
                self, lon, lat, strategy.value_or(gshhg::Thomas()),
                num_threads);
          },
          py::arg("lon"), py::arg("lat"), py::arg("strategy"),
          py::arg("num_threads") = 0)
      .def(
          "distance_to_nearest",
          [](const gshhg::GSHHG& self, const py::array_t<double>& lon,
             const py::array_t<double>& lat,
             const std::optional<gshhg::Vincenty>& strategy,
             const size_t num_threads) -> py::array_t<double> {
            return gshhg::distance_to_nearest(
                self, lon, lat, strategy.value_or(gshhg::Vincenty()),
                num_threads);
          },
          py::arg("lon"), py::arg("lat"), py::arg("strategy"),
          py::arg("num_threads") = 0)
      .def(
          "mask",
          [](const gshhg::GSHHG& self, const py::array_t<double>& lon,
             const py::array_t<double>& lat,
             const size_t num_threads) -> py::array_t<int8_t> {
            return gshhg::mask(self, lon, lat, num_threads);
          },
          py::arg("lon"), py::arg("lat"), py::arg("num_threads") = 0);
}