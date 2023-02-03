#include "geometry.hpp"

#include "math.hpp"

namespace gshhg {

// Global variables of Earth's geometric constants (WGS84)
// Equatorial Radius [m]
static const double A = 6378137;

// Polar radius [m]
static const double B = 6356752.3142;

// Eccentricity
const double E = std::sqrt((A * A - B * B) / (A * A));

// Second Eccentricity
const double SE = sqrt((A * A - B * B) / (B * B));

Cartesian geodetic_2_cartesian(const GeodeticRadian& point) {
  const auto cos_x = std::cos(point.get<0>());
  const auto sin_x = std::sin(point.get<0>());
  const auto cos_y = std::cos(point.get<1>());
  const auto sin_y = std::sin(point.get<1>());
  const auto chi = std::sqrt(1.0 - E * E * sin_y * sin_y);
  const auto a_chi = A / chi;

  return Cartesian(a_chi * cos_y * cos_x, a_chi * cos_y * sin_x,
                   (a_chi * (1.0 - E * E)) * sin_y);
}

GeodeticRadian cartesian_2_geodetic(const Cartesian& point) {
  auto x = point.get<0>();
  auto y = point.get<1>();
  auto z = point.get<2>();
  auto p = std::sqrt((x * x) + (y * y));
  auto theta = std::atan2((z * A), (p * B));

  /* Avoid 0 division error */
  if (x == 0.0 && y == 0.0) {
    return GeodeticRadian(0, std::copysign(pi_2<double>(), z));
  }

  auto lat = std::atan2((z + (SE * SE * B * std::pow(std::sin(theta), 3))),
                        (p - (E * E * A * std::pow(std::cos(theta), 3))));
  auto lon = std::atan2(y, x);

  return GeodeticRadian(lon, lat);
}

}  // namespace gshhg
