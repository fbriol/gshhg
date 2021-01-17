#include "gshhg.hpp"

#include <shapefil.h>

#include <boost/geometry/io/svg/svg_mapper.hpp>
#include <fstream>
#include <iostream>

namespace gshhg {

GSHHG::GSHHG(const std::string& dirname,
             const std::optional<std::string>& resolution,
             const std::optional<std::vector<int>>& levels,
             const std::optional<Box>& box) {
  auto resolution_ident =
      parse_resolution_string(resolution.value_or("intermediate"));
  auto resolution_code = std::string(1, static_cast<char>(resolution_ident));
  auto points = std::vector<Cartesian>();

  // For all hierarchical levels
  for (auto level = 1; level < 7; ++level) {
    // Does the user want to filter the levels to be loaded?
    if (levels) {
      const auto it = std::find(levels->begin(), levels->end(), level);
      if (it == levels->end()) {
        continue;
      }
    }

    // No boundary between pond-in-island and island in crude resolution
    if (resolution_ident == Resolution::kCrude && level == 4) {
      continue;
    }

    // Build the path to the ESRI shape files
    std::filesystem::path path =
        dirname / std::filesystem::path(resolution_code) /
        std::filesystem::path("GSHHS_" + resolution_code + "_L" +
                              std::to_string(level) + ".shp");

    // Load the hierarchical dataset selected
    load_shp(path.string(), level,
             // Level 5 at full resolution must be patched.
             resolution_ident == Resolution::kFull && level == 5, box, points);
  }
  rtree_.reset(new RTree(points));
}

void GSHHG::load_shp(const std::string& filename, const uint8_t level,
                     const bool patch, const std::optional<Box>& box,
                     std::vector<Cartesian>& points) {
  SHPHandle handle = SHPOpen(filename.c_str(), "rb");
  if (handle == nullptr) {
    throw std::system_error(ENOENT , std::system_category(), filename);
  }
  int shape_types, entities;
  double min_bound[4], max_bound[4];

  // Read file properties
  SHPGetInfo(handle, &entities, &shape_types, min_bound, max_bound);

  // Skim over the list of shapes
  for (int ix = 0; ix < entities; ++ix) {
    SHPObject* shape = SHPReadObject(handle, ix);
    if (shape == nullptr ||
        (shape->nParts > 0 && shape->panPartStart[0] != 0)) {
      SHPDestroyObject(shape);
      SHPClose(handle);
      throw std::runtime_error("unable to read shape " + std::to_string(ix));
    }

    if (shape->nSHPType == SHPT_POLYGON && shape->nVertices) {
      const auto* x = shape->padfX;
      const auto* y = shape->padfY;

      // Current polygon read
      auto polygon = Polygon();

      // Cartesian points read
      auto polygon_points = std::vector<Cartesian>();

      // Skim over vertices
      for (int jx = 0; jx < shape->nVertices; ++jx) {
        // Level 5 at full resolution must be patched(skip the two first points
        // and the last one).
        if (patch && ix == 0 && (jx < 2 || jx == shape->nVertices - 1)) {
          x++;
          y++;
          continue;
        }
        boost::geometry::append(polygon, Point(*x, *y));
        auto ecef =
            geodetic_2_cartesian(geodetic_2_radian(GeodeticDegree(*x++, *y++)));
        polygon_points.emplace_back(ecef);
      }

      // Level 5 at full resolution must be patched (close the polygon).
      if (patch && ix == 0) {
        boost::geometry::append(polygon, Point(180, -90));
        boost::geometry::append(polygon, Point(0, -90));
      }

      // Calculate the envelope of the current polygon
      auto envelope = Box();
      boost::geometry::envelope(polygon, envelope);

      // If the read polygon is located in the selected are
      if (box.has_value() ? boost::geometry::intersects(*box, envelope)
                          : true) {
        // We store the current polygon and its indexes
        polygons_.emplace_back(
            PolygonIndex{std::move(polygon), std::move(envelope), level});
        points.insert(points.end(),
                      std::make_move_iterator(polygon_points.begin()),
                      std::make_move_iterator(polygon_points.end()));
      }
    }
    SHPDestroyObject(shape);
  }
  SHPClose(handle);
}

void GSHHG::to_svg(const std::string& filename, const int width,
                   const int height) const {
  std::ofstream svg;
  svg.exceptions(std::ios_base::failbit | std::ios_base::badbit);
  svg.open(filename.c_str());

  boost::geometry::svg_mapper<Point> mapper(svg, width, height);
  mapper.add(Box({-180, -90}, {180, 90}));

  unsigned int index = 0;

  for (const auto& item : boost::adaptors::reverse(polygons_)) {
    auto rgb = (++index) % 0x1000000U;
    auto code = std::to_string((rgb >> 16U) & 0xFFU) + "," +
                std::to_string((rgb >> 8U) & 0xFFU) + "," +
                std::to_string(rgb & 0xFFU);
    mapper.add(item.polygon);
    mapper.map(item.polygon, "fill-opacity:0.5;fill:rgb(" + code +
                                 ");stroke:rgb(" + code + ")");
  }
}

}  // namespace gshhg