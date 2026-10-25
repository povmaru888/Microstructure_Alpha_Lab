#include "features.hpp"
#include <cmath>
int main() {
  microalpha::BookRow book{"d",0,0,{100.01},{300},{99.99},{900}};
  const auto row=microalpha::compute_l1(book);
  if (!row.midprice || std::abs(*row.midprice-100.0)>1e-12) return 1;
  if (!row.spread || std::abs(*row.spread-0.02)>1e-12) return 2;
  if (!row.obi_l1 || std::abs(*row.obi_l1-0.5)>1e-12) return 3;
  book.ask_sizes[0]=0; book.bid_sizes[0]=0;
  if (microalpha::compute_l1(book).obi_l1) return 4;
  return 0;
}
