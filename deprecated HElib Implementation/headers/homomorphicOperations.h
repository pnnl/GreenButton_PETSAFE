#ifndef HOMOMORPHICOPERATIONS_H
#define HOMOMORPHICOPERATIONS_H

#include "fileManager.h"

using namespace std;
using namespace helib;

/*****************************DEFINITIONS*******************************************/

unordered_map<string, string> encryptMeasurements(char* pathname,
                                                  const Context& context,
                                                  const PubKey& pk,
                                                  unordered_map<string, unordered_map
                                                               <string, unordered_map
                                                               <string, double>>> &measurements);

vector<double> decryption(const Context& context, const SecKey& sk, Ctxt c0);

Ctxt sumDataPoints(int numRows, const Context& context,const PubKey& pk, const SecKey& sk,
                   const string CIRCUITNAME,
                   const Ctxt c0);

void calculateDailyAverages(const int numRows, 
                            const Context& context,
                            const SecKey& sk,
                            const PubKey& pk,
                            const unordered_map<string, string> FILENAMES);


/*****************************IMPLEMENTATIONS**************************************/

unordered_map<string, string> encryptMeasurements(char* pathname,
                                                  const Context& context,
                                                  const PubKey& pk,
                                                  unordered_map<string, unordered_map
                                                               <string, map
                                                               <string, double>>> &measurements){

    
    unordered_map<string, string> ctxtFilenames;
    for (auto eeSiteID : measurements){
        for (auto regname : eeSiteID.second){
            int counter = 0;
            vector<double> circuitMeasurements(context.getNSlots());

            for (auto datetime : regname.second){
                circuitMeasurements[counter] = datetime.second;
                counter++;
            }
            //The plaintext vector is loaded into a special type of 
            //container (PtxtArray) that is associated with a Context object.
            PtxtArray p0(context, circuitMeasurements);

            //Constructing the ciphertext that will be associated with the PubKey object.
            Ctxt c0(pk);
            p0.encrypt(c0);
            string filename = string(pathname) + "/" + regname.first + "-" + eeSiteID.first + ".txt";
            fstream outCtxtFile(filename, std::ios::out | std::ios::in | std::ios::trunc);

            if (outCtxtFile.is_open()) {
                c0.writeToJSON(outCtxtFile);
                outCtxtFile.close();
                ctxtFilenames[regname.first] = filename;
            } 
            else {
                throw std::runtime_error("Could not open file " + filename + ".json.");
            }
        }
    }
    measurements.clear();
    return ctxtFilenames;
}


vector<double> decryption(const Context& context, const SecKey& sk, Ctxt c0){
    vector<double> v3;
    PtxtArray pp3(context);
    pp3.decrypt(c0, sk);
    pp3.store(v3); 

    return v3;
}

Ctxt sumDataPoints(const int numRows, const Context& context,
                   const PubKey& pk, const SecKey& sk,
                   const string CIRCUITNAME,
                   const Ctxt c0)
{
  Ctxt c1 = c0;
  Ctxt c2 = c0;
  int bounds = numRows * -1;

  for (int i = -1; i > bounds; i--){
    rotate(c1, -1);
    c2 += c1;
  }


  if (CIRCUITNAME == std::string("Mains")){
    vector<double> sums = decryption(context, sk, c2);

    for (int i = 0; i < numRows; i++){
        if (int(sums[i]) != 0){
            sums[i] = 1 / sums[i];
            }
        }
        
    PtxtArray p0(context, sums);
    Ctxt c3(pk);
    p0.encrypt(c3);

    return c3;
  }
  
  return c2;
}


void calculateDailyAverages(int numRows, 
                            const Context& context,
                            const SecKey& sk,
                            const PubKey& pk,
                            const unordered_map<string, string> FILENAMES)
{  
    Ctxt c0 = readCtxtFile(context, pk, FILENAMES.at("Mains"));
    Ctxt total = sumDataPoints(numRows, context, pk, sk, "Mains", c0);

    for (auto filename : FILENAMES){
        if (filename.first != std::string("Mains")){
            Ctxt c1 = readCtxtFile(context, pk, filename.second);
            cout << filename.first << endl;
            Ctxt circuitSum = sumDataPoints(numRows, context, pk, sk, filename.first, c1);
            circuitSum *= total;
            vector<double> res = decryption(context, sk, circuitSum);
            cout << res[0] << endl;
        }
    }
}

void test2(const Context& context, SecKey& sk, const PubKey& pk){
    Ctxt c1 = readCtxtFile(context, pk, "c1.json");
    Ctxt c2 = readCtxtFile(context, pk, "c2.json");
    Ctxt c3 = c1;
    c3 *= c2;

    PtxtArray pp0(context);
    pp0.decrypt(c3, sk);
    vector<double>v3;
    pp0.store(v3);

    cout << v3[1] << endl;
}

void mult(const Context& context, const PubKey& pk, SecKey& sk){
    vector<double>v1 = {270.61, 12.3, 10.1};
    vector<double>v2 = {61.23, 10.3, 27.9};

    PtxtArray p0(context, v1);
    PtxtArray p1(context, v2);

    Ctxt c1(pk);
    Ctxt c2(pk);

    p0.encrypt(c1);
    p1.encrypt(c2);

    writeCtxtFile("c1.json", c1);
    writeCtxtFile("c2.json", c2);

    test2(context, sk, pk);
}

#endif