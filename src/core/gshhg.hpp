#pragma once
#include <filesystem>
#include <memory>
#include <optional>
#include <string>
#include <tuple>
#include <vector>

#include "geometry.hpp"

namespace gshhg {

class GSHHG {
 public:
  // The GSHHG geography data set resolution
  enum class Resolution : char {
    kCrude = 'c',
    kLow = 'l',
    kIntermediate = 'i',
    kHigh = 'h',
    kFull = 'f'
  };

  // Default constructor
  GSHHG(const std::string& dirname,
        const std::optional<std::string>& resolution,
        const std::optional<std::vector<int>>& levels,
        std::optional<Box> bbox);

  // Gets the number of points handled
  [[nodiscard]] inline auto points() const -> size_t { return rtree_->size(); }

  // Gets the number of polygon handled
  [[nodiscard]] inline auto polygons() const -> size_t {
    return polygons_.size();
  }

  // Gets the level of the polygon in which the given point is located or zero
  // if the point is located outside of all the handled polygons.
  [[nodiscard]] inline auto mask(const double lon, const double lat) const
      -> uint8_t {
    auto point = Point(normalize_angle(lon, -180.0, 360.0), lat);

    for (const auto& item : boost::adaptors::reverse(polygons_)) {
      if (boost::geometry::intersects(point, item.envelope) &&
          boost::geometry::intersects(point, item.polygon)) {
        return item.level;
      }
    }
    return 0;
  }

  // Gets the nearest point of one of the handled polygons.
  [[nodiscard]] inline auto nearest(const double lon, const double lat) const
      -> GeodeticDegree {
    const auto ecef = geodetic_2_cartesian(geodetic_2_radian({lon, lat, 0}));
    return geodetic_2_degree(cartesian_2_geodetic(nearest(ecef)));
  }

  // Gets the distance of the nearest point
  template <class Strategy>
  [[nodiscard]] inline auto distance_to_nearest(
      const double lon, const double lat, const Strategy& strategy) const
      -> double {
    return boost::geometry::distance(nearest(lon, lat),
                                     GeodeticDegree{lon, lat}, strategy);
  }

  // Create the SVG figure of the handled polygons.
  auto to_svg(const std::string& filename, const int width,
              const int height) const -> void;

 private:
  // Structure indexing the loaded polygons.
  struct PolygonIndex {
    Polygon polygon;
    Box envelope;
    uint8_t level;
  };

  // Parse the resolution string
  static Resolution parse_resolution_string(const std::string& resolution) {
    if (resolution == "crude") {
      return Resolution::kCrude;
    }
    if (resolution == "low") {
      return Resolution::kLow;
    }
    if (resolution == "intermediate") {
      return Resolution::kIntermediate;
    }
    if (resolution == "high") {
      return Resolution::kHigh;
    }
    if (resolution == "full") {
      return Resolution::kFull;
    }
    throw std::invalid_argument("resolution '" + resolution +
                                "' is not defined");
  }

  // Load the shapefile selected
  void load_shp(const std::string& filename, uint8_t level, bool patch,
                std::vector<Cartesian>& points);

  [[nodiscard]] inline auto nearest(const Cartesian& point) const -> Cartesian {
    auto result = std::vector<Cartesian>();
    std::for_each(rtree_->qbegin(boost::geometry::index::nearest(point, 1)),
                  rtree_->qend(),
                  [&result](const auto& item) { result.emplace_back(item); });
    return result.at(0);
  }

  // Bounding box loaded
  std::optional<Box> bbox_;

  // List of polygons read: envelope, polygon and level
  std::vector<PolygonIndex> polygons_{};
  using RTree =
      boost::geometry::index::rtree<Cartesian,
                                    boost::geometry::index::rstar<16>>;
  std::unique_ptr<RTree> rtree_{nullptr};
};

}  // namespace gshhg