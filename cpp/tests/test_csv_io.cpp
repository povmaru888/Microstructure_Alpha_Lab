#include "csv_io.hpp"
#include <sstream>
#include <stdexcept>
int main() {
  std::istringstream good("dataset_id,event_index,research_index,ask_price_1,ask_size_1,bid_price_1,bid_size_1\nd,4,3,101,20,99,30\n");
  const auto rows = microalpha::read_books_csv(good, 1);
  if (rows.size() != 1 || rows[0].dataset_id != "d" || rows[0].event_index != 4) return 1;
  std::ostringstream output;
  microalpha::FeatureRow feature; feature.dataset_id="d"; feature.event_index=4; feature.research_index=3;
  microalpha::write_features_csv(output, {feature});
  if (output.str().find("d,4,3,") == std::string::npos) return 2;
  try { std::istringstream bad("bad\n"); microalpha::read_books_csv(bad, 1); }
  catch (const std::runtime_error&) { return 0; }
  return 3;
}
