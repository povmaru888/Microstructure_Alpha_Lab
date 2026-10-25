#include "features.hpp"
#include <deque>
#include <numeric>
#include <stdexcept>
namespace microalpha {
double midpoint(const BookTop& book) { return (book.bid_price + book.ask_price) / 2.0; }
FeatureRow compute_l1(const BookRow& book) {
  if (book.ask_prices.empty() || book.bid_prices.empty()) throw std::invalid_argument("book has no L1");
  FeatureRow row; row.dataset_id=book.dataset_id; row.event_index=book.event_index; row.research_index=book.research_index;
  const double mid=(book.bid_prices[0]+book.ask_prices[0])/2.0;
  if (mid > 0) { row.midprice=mid; row.spread=book.ask_prices[0]-book.bid_prices[0]; row.relative_spread=*row.spread/mid; }
  const double total=book.bid_sizes[0]+book.ask_sizes[0];
  if (total > 0) row.obi_l1=(book.bid_sizes[0]-book.ask_sizes[0])/total;
  add_microprice(row, book);
  return row;
}
void add_microprice(FeatureRow& row, const BookRow& book) {
  const double total=book.bid_sizes[0]+book.ask_sizes[0];
  if (total <= 0 || !row.midprice || *row.midprice <= 0) return;
  row.microprice=(book.ask_prices[0]*book.bid_sizes[0]+book.bid_prices[0]*book.ask_sizes[0])/total;
  row.micro_deviation=(*row.microprice-*row.midprice)/ *row.midprice;
}
double event_ofi(const BookRow& previous, const BookRow& current) {
  double value=0;
  if (current.bid_prices[0]>=previous.bid_prices[0]) value+=current.bid_sizes[0];
  if (current.bid_prices[0]<=previous.bid_prices[0]) value-=previous.bid_sizes[0];
  if (current.ask_prices[0]<=previous.ask_prices[0]) value-=current.ask_sizes[0];
  if (current.ask_prices[0]>=previous.ask_prices[0]) value+=previous.ask_sizes[0];
  return value;
}
namespace {
std::optional<double> depth_obi(const BookRow& book, std::size_t depth) {
  if (book.bid_sizes.size()<depth || book.ask_sizes.size()<depth) return std::nullopt;
  double bid=0, ask=0;
  for (std::size_t i=0;i<depth;++i) { bid+=book.bid_sizes[i]; ask+=book.ask_sizes[i]; }
  return bid+ask>0 ? std::optional<double>((bid-ask)/(bid+ask)) : std::nullopt;
}
std::optional<double> rolling(const std::deque<double>& values, std::size_t window) {
  if (values.size()<window) return std::nullopt;
  return std::accumulate(values.end()-static_cast<long>(window),values.end(),0.0);
}
}
std::vector<FeatureRow> compute_features(const std::vector<BookRow>& books) {
  std::vector<FeatureRow> output; output.reserve(books.size()); std::deque<double> events;
  for (std::size_t index=0;index<books.size();++index) {
    auto row=compute_l1(books[index]);
    row.obi_l5=depth_obi(books[index],5); row.obi_l10=depth_obi(books[index],10);
    if (index>0) { row.ofi_event=event_ofi(books[index-1],books[index]); events.push_back(*row.ofi_event); }
    row.ofi_w10=rolling(events,10); row.ofi_w20=rolling(events,20); row.ofi_w50=rolling(events,50);
    if (events.size()>50) events.pop_front();
    output.push_back(std::move(row));
  }
  return output;
}
}
