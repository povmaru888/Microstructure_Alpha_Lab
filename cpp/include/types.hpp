#pragma once

#include <optional>
#include <string>
#include <vector>

namespace microalpha {
struct BookTop {
  double bid_price{};
  double ask_price{};
  double bid_size{};
  double ask_size{};
};
struct BookRow {
  std::string dataset_id;
  long long event_index{};
  long long research_index{};
  std::vector<double> ask_prices, ask_sizes, bid_prices, bid_sizes;
};
struct FeatureRow {
  std::string dataset_id;
  long long event_index{};
  long long research_index{};
  std::optional<double> midprice, spread, relative_spread, obi_l1, obi_l5, obi_l10,
      microprice, micro_deviation, ofi_event, ofi_w10, ofi_w20, ofi_w50;
};
}
