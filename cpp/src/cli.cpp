#include "cli.hpp"
#include "csv_io.hpp"
#include "features.hpp"
#include <filesystem>
#include <chrono>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
namespace microalpha {
int run_cli(int argc, char** argv) {
  std::filesystem::path input, output; int levels=10; bool force=false, timing=false;
  for (int index=1;index<argc;++index) {
    const std::string arg=argv[index];
    if ((arg=="--input" || arg=="--output" || arg=="--levels") && index+1>=argc) { std::cerr<<"missing value for "<<arg<<'\n'; return 2; }
    if (arg=="--input") input=argv[++index]; else if (arg=="--output") output=argv[++index]; else if (arg=="--levels") levels=std::stoi(argv[++index]); else if (arg=="--force") force=true; else if (arg=="--timing") timing=true; else { std::cerr<<"unknown argument: "<<arg<<'\n'; return 2; }
  }
  if (input.empty() || output.empty()) { std::cerr<<"--input and --output are required\n"; return 2; }
  if (std::filesystem::exists(output) && !force) { std::cerr<<"output exists; use --force\n"; return 5; }
  try {
    const auto start=std::chrono::steady_clock::now();
    std::ifstream source(input); if (!source) throw std::runtime_error("cannot open input");
    const auto books=read_books_csv(source,levels); const auto parsed=std::chrono::steady_clock::now();
    const auto features=compute_features(books); const auto computed=std::chrono::steady_clock::now();
    const auto temporary=output.string()+".tmp"; std::ofstream destination(temporary); if (!destination) throw std::runtime_error("cannot open output");
    destination.precision(17); write_features_csv(destination,features); destination.close();
    if (force && std::filesystem::exists(output)) std::filesystem::remove(output);
    std::filesystem::rename(temporary,output);
    const auto written=std::chrono::steady_clock::now();
    if (timing) {
      const std::chrono::duration<double> parse=parsed-start, compute=computed-parsed, write=written-computed;
      std::cerr<<"TIMING parse="<<parse.count()<<" compute="<<compute.count()<<" write="<<write.count()<<'\n';
    }
  } catch (const std::exception& error) { std::cerr<<error.what()<<'\n'; return 3; }
  return 0;
}
}
