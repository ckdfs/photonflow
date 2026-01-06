/**
 * @file common.hpp
 * @brief Common definitions and includes for PhotonFlow.
 *
 * This header should be included FIRST in all source files to ensure
 * proper macro definitions on all platforms.
 */

#pragma once

// MSVC requires these before <cmath> for M_PI, M_E, etc.
#ifndef _USE_MATH_DEFINES
#define _USE_MATH_DEFINES
#endif

#ifndef NOMINMAX
#define NOMINMAX
#endif

#include <cmath>

// Fallback M_PI definition if not provided by platform
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#ifndef M_E
#define M_E 2.71828182845904523536
#endif
