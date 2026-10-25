#pragma once
#include "types.hpp"
#include <vector>
namespace microalpha {
double midpoint(const BookTop& book);
FeatureRow compute_l1(const BookRow& book);
void add_microprice(FeatureRow& row, const BookRow& book);
double event_ofi(const BookRow& previous, const BookRow& current);
std::vector<FeatureRow> compute_features(const std::vector<BookRow>& books);
}
