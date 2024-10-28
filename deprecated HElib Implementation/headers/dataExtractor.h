#ifndef DATAEXTRACTOR_H
#define DATAEXTRACTOR_H

#include <arrow/api.h>
#include <arrow/csv/api.h>
#include <arrow/io/api.h>
#include <arrow/ipc/api.h>
#include <string>
#include <map>
#include <unordered_map>

using namespace std;

arrow::Status extractCircuits(string filename, string siteID, 
                              unordered_map<string, string> &circuits);

arrow::Status extractMeasurements(string filename, string siteID, 
                                  unordered_map<string, string> circuits, 
                                  unordered_map<string, unordered_map
                                               <string, map
                                               <string, double>>> &measurements);


arrow::Status extractCircuits(string filename, string siteID, 
                              unordered_map<string, string> &circuits)
{
    //A ReableFile object is created to point all readers to the 
    //correct data on the disk. It can be used to rebind multiple files.
    std::shared_ptr<arrow::io::ReadableFile> infile;

    //The input is bound to the file contained in the 'filename' argument.
    ARROW_ASSIGN_OR_RAISE(infile, arrow::io::ReadableFile::Open(filename));
    std::shared_ptr<arrow::Table> csv_table;

    //Using the default options for the CSV reader.
    ARROW_ASSIGN_OR_RAISE(
        auto csv_reader,
        arrow::csv::TableReader::Make(
            arrow::io::default_io_context(), infile, arrow::csv::ReadOptions::Defaults(),
            arrow::csv::ParseOptions::Defaults(), arrow::csv::ConvertOptions::Defaults()));

    ARROW_ASSIGN_OR_RAISE(csv_table, csv_reader->Read());

    //string eeSiteID = "";
    std::shared_ptr<arrow::ChunkedArray> eeSiteIdData = csv_table->GetColumnByName("ee_site_id");
    std::shared_ptr<arrow::ChunkedArray> regname = csv_table->GetColumnByName("regname");
    
    for (int i = 0; i < csv_table->num_rows(); i++)
    {
      string eeSiteID = eeSiteIdData->GetScalar(i)->get()->ToString();

      if (eeSiteID == std::string(siteID)){
        string circuitLabel = csv_table->GetColumnByName("circuit_label")->GetScalar(i)->get()->ToString();

        if (circuitLabel.find(std::string("heat")) != std::string::npos || 
            circuitLabel.find(std::string("Heat")) != std::string::npos){
          circuits[regname->GetScalar(i)->get()->ToString()] = "";
        }
        else if (circuitLabel.find(std::string("Mains")) != std::string::npos){
          circuits[regname->GetScalar(i)->get()->ToString()] = "";
        }
      }
    }
    return arrow::Status::OK();
}


arrow::Status extractMeasurements(string filename, string siteID, 
                                  unordered_map<string, string> circuits, 
                                  unordered_map<string, unordered_map
                                               <string, map
                                               <string, double>>> &measurements)
{
      //A ReableFile object is created to point all readers to the 
    //correct data on the disk. It can be used to rebind multiple files.
    std::shared_ptr<arrow::io::ReadableFile> infile;

    //The input is bound to the file contained in the 'filename' argument.
    ARROW_ASSIGN_OR_RAISE(infile, arrow::io::ReadableFile::Open(filename));
    std::shared_ptr<arrow::Table> csv_table;

    //Using the default options for the CSV reader.
    ARROW_ASSIGN_OR_RAISE(
        auto csv_reader,
        arrow::csv::TableReader::Make(
            arrow::io::default_io_context(), infile, arrow::csv::ReadOptions::Defaults(),
            arrow::csv::ParseOptions::Defaults(), arrow::csv::ConvertOptions::Defaults()));

    ARROW_ASSIGN_OR_RAISE(csv_table, csv_reader->Read());

    //string eeSiteID = "";
    std::shared_ptr<arrow::ChunkedArray> eeSiteIdData = csv_table->GetColumnByName("ee_site_id");
    std::shared_ptr<arrow::ChunkedArray> regname = csv_table->GetColumnByName("regname");
    
    for (int i = 0; i < csv_table->num_rows(); i++)
    {
      string eeSiteID = eeSiteIdData->GetScalar(i)->get()->ToString();

      if (eeSiteID == std::string(siteID)){
        string regname = csv_table->GetColumnByName("regname")->GetScalar(i)->get()->ToString();

        if (circuits.find(regname) != circuits.end()){
          string startDatetime = csv_table->GetColumnByName("min_t")->GetScalar(i)->get()->ToString();
          string endDatetime = csv_table->GetColumnByName("max_t")->GetScalar(i)->get()->ToString();
          string interval = startDatetime + " - " + endDatetime;

          double measurement = atof(csv_table->GetColumnByName("power")->GetScalar(i)->get()->ToString().c_str());

          if ((int)measurement <= 0){
            measurements[siteID][regname][interval] = 0.0;
          }
          else {
            measurements[siteID][regname][interval] = measurement;
          }
        }
      }
    }
    return arrow::Status::OK();
}

#endif