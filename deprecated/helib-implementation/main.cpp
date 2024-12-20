//#include <helib/helib.h>
//#include <fstream>
//#include <iostream>
//#include <string>
//#include <stdio.h>
//#include <sstream>
//#include <vector>
//#include<unistd.h> 
//#include <map>
//#include <stdlib.h>
//#include <time.h>
//#include <bits/stdc++.h>
//#include <sys/stat.h>
//#include <sys/types.h>
#include <unordered_map>
#include <helib/helib.h>
#include "headers/dataExtractor.h"
#include "headers/fileManager.h"
#include "headers/homomorphicOperations.h"

using namespace std;
using namespace helib;

int parseArgs(int argc, char* argv[],
              unordered_map<string, string>& args){
    for (int i = 0; i < argc; i++){
        if (argv[i] == std::string("-d") && i + 1 < argc){
            args["dataset"] = argv[i + 1];
        }
        else if (argv[i] == std::string("-i") && i + 1 < argc){
            args["siteID"] = argv[i + 1];
        }
        else if (argv[i] == std::string("-p") && i + 1 < argc){
            args["points"] = argv[i + 1];
        }
    }

    if (args["dataset"] == std::string("")){
        cout << "Error! No filename for dataset specified.\n";
        return -1;
        }
    if (args["points"] == std::string("")){
        cout << "Error! No filename for points data specified.\n";
        return -1;
        }
    if (args["siteID"] == std::string("")){
        cout << "Error! No site ID provided.\n";
        return -1;
        }
    return 1;
}

unsigned int countDatapoints(unordered_map<string, unordered_map
                                          <string, map
                                          <string, double>>> &measurements){
  for (auto i : measurements){
    for (auto j : i.second){
      return j.second.size();
    }
  }
  return 0;
}

int main(int argc, char* argv[]){
    unordered_map<string, string> args;
    args["dataset"] = "";
    args["points"] = "";
    args["siteID"] = "";

    if (parseArgs(argc, argv, args) < 0){ return -1;}

    //measurements[EE_SITE_ID][REGNAME][DATETIME] = Measurement during that time interval.
    unordered_map<string, unordered_map<string, map<string, double>>> measurements;

    //circuits[EE_SITE_ID][REGNAME] = DATETIME
    unordered_map<string, string> circuits;

    unordered_map<string, string> ctxtFilenames;
    char* pathname = createDir("circuitData"); 

    const Context context = ContextBuilder<CKKS>().m(2 * 1024).bits(119).precision(20).c(2).build();  

    //Construct a secret key that is associated with a specific Context. 
    SecKey sk(context);
    //Builds a full-fledged secret key. 
    sk.GenSecKey();
    addSome1DMatrices(sk);

    const PubKey& pk = sk;

    char* configPath = createDir("configuration");

    writeContextFile(string(configPath) + "/context.json", context);
    writeSkFile(string(configPath) + "/sk.json", sk);
    writePkFile(string(configPath) + "/pk.json", pk);

    vector<double> v0 = {1.1, 2.1, 3.1};
    PtxtArray p0(context, v0);
    Ctxt c0(pk);
    p0.encrypt(c0);
    
    arrow::Status st1 = extractCircuits(args["points"], args["siteID"], circuits);
    arrow::Status st2 = extractMeasurements(args["dataset"], args["siteID"],
                                            circuits, measurements);
    int numRows = countDatapoints(measurements);

    ctxtFilenames = encryptMeasurements(pathname, context, pk, measurements);
    calculateDailyAverages(numRows, context, sk, pk, ctxtFilenames);
    

    return 0;
}