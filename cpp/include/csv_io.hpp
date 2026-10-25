#pragma once
#include "types.hpp"
#include <istream>
#include <ostream>
#include <vector>
namespace microalpha {
std::vector<BookRow> read_books_csv(std::istream& input, int levels);
void write_features_csv(std::ostream& output, const std::vector<FeatureRow>& rows);
}
