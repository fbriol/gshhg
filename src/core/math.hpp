#pragma once
#include <cmath>

namespace gshhg {

/// π
template <typename T>
inline constexpr auto pi() noexcept -> T {
  return std::atan2(T(0), T(-1));
}

/// π/2
template <typename T>
inline constexpr auto pi_2() noexcept -> T {
  return 0.5 * pi<T>();
}

/// 2π
template <typename T>
inline constexpr auto two_pi() noexcept -> T {
  return T(2) * pi<T>();
}

/// Convert angle x from radians to degrees.
template <typename T>
inline constexpr auto radians(const T& x) noexcept -> T {
  return x * pi<T>() / T(180);
}

/// Convert angle x from degrees to radians.
template <typename T>
inline constexpr auto degrees(const T& x) noexcept -> T {
  return x * T(180) / pi<T>();
}

/// Computes the remainder of the operation x/y
///
/// @return a result with the same sign as its second operand
template <typename T, typename std::enable_if<std::is_integral<T>::value,
                                              T>::type* = nullptr>
inline constexpr auto remainder(const T& x, const T& y) noexcept -> T {
  auto result = x % y;
  return result != 0 && (result ^ y) < 0 ? result + y : result;
}

/// Computes the remainder of the operation x/y
///
/// @return a result with the same sign as its second operand
template <typename T, typename std::enable_if<std::is_floating_point<T>::value,
                                              T>::type* = nullptr>
inline constexpr auto remainder(const T& x, const T& y) noexcept -> T {
  auto result = std::remainder(x, y);
  if (result < T(0)) {
    result += y;
  }
  return result;
}

/// Normalize an angle.
///
/// @param x The angle in degrees.
/// @param min Minimum circle value
/// @param circle Circle value
/// @return the angle reduced to the range [min, circle + min[
template <typename T>
inline constexpr auto normalize_angle(const T& x, const T& min,
                                      const T& circle) noexcept -> T {
  return remainder(x - min, circle) + min;
}

}  // namespace gshhg
