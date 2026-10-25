#include "features.hpp"
#include <cmath>
int main() {
  microalpha::BookRow before{"d",0,0,{101},{300},{99},{900}};
  auto row=microalpha::compute_l1(before);
  if (!row.microprice || *row.microprice < 99 || *row.microprice > 101) return 1;
  microalpha::BookRow after{"d",1,1,{101},{280},{100},{950}};
  const double expected=950-280+300;
  if (std::abs(microalpha::event_ofi(before,after)-expected)>1e-12) return 2;
  microalpha::FeatureRow first=microalpha::compute_l1(before);
  if (first.ofi_event) return 3;
  return 0;
}
