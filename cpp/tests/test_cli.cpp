#include "cli.hpp"
#include <filesystem>
#include <fstream>
#include <string>
int main() {
  const auto root=std::filesystem::temp_directory_path()/"microalpha_cli_test"; std::filesystem::create_directories(root);
  const auto input=root/"input.csv", output=root/"output.csv";
  { std::ofstream file(input); file<<"dataset_id,event_index,research_index,ask_price_1,ask_size_1,bid_price_1,bid_size_1\nd,0,0,101,300,99,900\n"; }
  std::string a0="tool", a1="--input", a2=input.string(), a3="--output", a4=output.string(), a5="--levels", a6="1";
  char* args[]={a0.data(),a1.data(),a2.data(),a3.data(),a4.data(),a5.data(),a6.data()};
  std::filesystem::remove(output);
  if (microalpha::run_cli(7,args)!=0 || !std::filesystem::exists(output)) return 1;
  if (microalpha::run_cli(7,args)!=5) return 2;
  std::filesystem::remove_all(root); return 0;
}
