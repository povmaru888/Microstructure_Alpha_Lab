#include "csv_io.hpp"
#include <sstream>
#include <stdexcept>
#include <string>

namespace {
std::vector<std::string> split(const std::string& line) {
  std::vector<std::string> fields;
  std::stringstream stream(line);
  std::string field;
  while (std::getline(stream, field, ',')) fields.push_back(field);
  return fields;
}
void value(std::ostream& output, const std::optional<double>& item) {
  if (item) output << *item;
}
}
namespace microalpha {
std::vector<BookRow> read_books_csv(std::istream& input, int levels) {
  if (levels <= 0) throw std::invalid_argument("levels must be positive");
  std::string line;
  if (!std::getline(input, line)) throw std::runtime_error("missing CSV header");
  const auto header = split(line);
  if (header.size() != static_cast<std::size_t>(3 + 4 * levels) || header[0] != "dataset_id" || header[1] != "event_index" || header[2] != "research_index")
    throw std::runtime_error("invalid canonical CSV header");
  std::vector<BookRow> rows;
  while (std::getline(input, line)) {
    if (line.empty()) continue;
    const auto fields = split(line);
    if (fields.size() != header.size()) throw std::runtime_error("invalid canonical CSV row width");
    BookRow row{fields[0], std::stoll(fields[1]), std::stoll(fields[2])};
    for (int level = 0; level < levels; ++level) {
      const auto offset = 3 + 4 * level;
      row.ask_prices.push_back(std::stod(fields[offset]));
      row.ask_sizes.push_back(std::stod(fields[offset + 1]));
      row.bid_prices.push_back(std::stod(fields[offset + 2]));
      row.bid_sizes.push_back(std::stod(fields[offset + 3]));
    }
    rows.push_back(std::move(row));
  }
  return rows;
}
void write_features_csv(std::ostream& output, const std::vector<FeatureRow>& rows) {
  output << "dataset_id,event_index,research_index,midprice,spread,relative_spread,obi_l1,obi_l5,obi_l10,microprice,micro_deviation,ofi_event,ofi_w10,ofi_w20,ofi_w50\n";
  for (const auto& row : rows) {
    output << row.dataset_id << ',' << row.event_index << ',' << row.research_index << ',';
    const std::optional<double> values[] = {row.midprice,row.spread,row.relative_spread,row.obi_l1,row.obi_l5,row.obi_l10,row.microprice,row.micro_deviation,row.ofi_event,row.ofi_w10,row.ofi_w20,row.ofi_w50};
    for (std::size_t index = 0; index < 12; ++index) { value(output, values[index]); output << (index == 11 ? '\n' : ','); }
  }
}
}
