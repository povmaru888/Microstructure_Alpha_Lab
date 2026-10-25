#include "features.hpp"
#include <cmath>
int main() { return std::abs(microalpha::midpoint({99.0, 101.0, 1.0, 1.0}) - 100.0) < 1e-12 ? 0 : 1; }
