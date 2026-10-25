#include "features.hpp"
#include <cmath>
#include <vector>
int main() {
  std::vector<microalpha::BookRow> books;
  for (int i=0;i<60;++i) {
    microalpha::BookRow book; book.dataset_id="d"; book.event_index=i; book.research_index=i;
    for (int level=1;level<=10;++level) { book.ask_prices.push_back(100+level*.01); book.ask_sizes.push_back(300); book.bid_prices.push_back(100-level*.01); book.bid_sizes.push_back(900); }
    books.push_back(book);
  }
  const auto rows=microalpha::compute_features(books);
  if (!rows[0].obi_l5 || std::abs(*rows[0].obi_l5-.5)>1e-12) return 1;
  if (rows[9].ofi_w10 || !rows[10].ofi_w10) return 2;
  if (rows[49].ofi_w50 || !rows[50].ofi_w50) return 3;
  return 0;
}
