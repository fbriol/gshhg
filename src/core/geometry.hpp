#pragma once
#include <boost/geometry.hpp>

#include "math.hpp"

namespace gshhg {

using Cartesian =
    boost::geometry::model::point<double, 3, boost::geometry::cs::cartesian>;
using GeodeticDegree = boost::geometry::model::point<
    double, 3, boost::geometry::cs::geographic<boost::geometry::degree>>;
using GeodeticRadian = boost::geometry::model::point<
    double, 3, boost::geometry::cs::geographic<boost::geometry::radian>>;
using Point =
    boost::geometry::model::point<double, 2, boost::geometry::cs::cartesian>;

using Box = boost::geometry::model::box<Point>;
using Polygon = boost::geometry::model::polygon<Point>;

using Spheroid = boost::geometry::srs::spheroid<double>;

using Andoyer = boost::geometry::strategy::distance::andoyer<Spheroid>;
using Haversine = boost::geometry::strategy::distance::haversine<Spheroid>;
using Thomas = boost::geometry::strategy::distance::thomas<Spheroid>;
using Vincenty = boost::geometry::strategy::distance::vincenty<Spheroid>;


GeodeticRadian cartesian_2_geodetic(const Cartesian& point);
Cartesian geodetic_2_cartesian(const GeodeticRadian& point);

inline GeodeticRadian geodetic_2_radian(const GeodeticDegree& point) {
  return GeodeticRadian(radians(point.get<0>()), radians(point.get<1>()),
                        point.get<2>());
}

inline GeodeticDegree geodetic_2_degree(const GeodeticRadian& point) {
  return GeodeticDegree(degrees(point.get<0>()), degrees(point.get<1>()),
                        point.get<2>());
}

}  // namespace gshhg
