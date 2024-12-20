#ifndef FILEMANAGER_H
#define FILEMANAGER_H

#include <helib/helib.h>
#include <bits/stdc++.h>
#include <sys/stat.h>
#include <fstream>
#include <iostream>
#include <string>
#include <stdio.h>
#include <sstream>
#include<unistd.h> 
#include <stdlib.h>
#include <bits/stdc++.h>
#include <sys/stat.h>
#include <sys/types.h>

using namespace std;
using namespace helib;

void writeContextFile(string fileName, const Context& context);
void writeSkFile(string fileName, SecKey sk);
void writePkFile(string fileName, PubKey pk);
void writeCtxtFile(string fileName, Ctxt ctxt);

Context readContextFile(string pathname);
PubKey readPkFile(const Context& context, string pathname);
SecKey readSkFile(const Context& context, string pathname);
Ctxt readCtxtFile(Context& context, const PubKey& pk, string pathname);

char* createDir(string dirName);

void writeContextFile(string fileName, const Context& context){
    ofstream outContextFile;
    outContextFile.open(fileName, std::ios::out);

    if (outContextFile.is_open()){
        context.writeToJSON(outContextFile);
        outContextFile.close();
        } 
    }

void writeSkFile(string fileName, SecKey sk){
    ofstream outSkFile;
    outSkFile.open(fileName, std::ios::out);

    if (outSkFile.is_open()){
        sk.writeToJSON(outSkFile);
        outSkFile.close();
        } 
}
void writePkFile(string fileName, PubKey pk){
    ofstream outPkFile;
    outPkFile.open(fileName, std::ios::out);

    if (outPkFile.is_open()){
        pk.writeToJSON(outPkFile);
        outPkFile.close();
        } 
}

void writeCtxtFile(string fileName, Ctxt ctxt){
    ofstream outCtxtFile;
    outCtxtFile.open(fileName, std::ios::out);

    if (outCtxtFile.is_open()){
        ctxt.writeToJSON(outCtxtFile);
        outCtxtFile.close();
        } 
}

Context readContextFile(string pathname){
    ifstream contextFile;
    contextFile.open(pathname);

    if (contextFile.is_open()){
        return Context::readFromJSON(contextFile);
    }
    else
    {
        throw std::runtime_error("Error! Could not open " + pathname);
    }  
}

PubKey readPkFile(const Context& context, string pathname){
    ifstream pkFile;
    pkFile.open(pathname);

    if (pkFile.is_open()){
        PubKey temp = PubKey::readFromJSON(pkFile, context);
        pkFile.close();
        return temp;
    }
    else
    {
        throw std::runtime_error("Error! Could not open " + pathname);
    }  
}

SecKey readSkFile(const Context& context, string pathname){
    ifstream skFile;
    skFile.open(pathname);

    if (skFile.is_open()){
        SecKey temp = SecKey::readFromJSON(skFile, context);
        skFile.close();
        return temp;
    }
    else
    {
        throw std::runtime_error("Error! Could not open " + pathname);
    }  
}

Ctxt readCtxtFile(const Context& context, const PubKey& pk, string pathname){
    ifstream ctxtFile;
    ctxtFile.open(pathname);

    if (ctxtFile.is_open()){
        Ctxt temp = Ctxt::readFromJSON(ctxtFile, pk);
        ctxtFile.close();
        return temp;
    }
    else
    {
        throw std::runtime_error("Error! Could not open " + pathname);
    }  
}

char* createDir(string dirName){
    string strPath = filesystem::current_path()/dirName;
    char* pathname = new char[strPath.size()];

    for (int i = 0; i < strPath.size() + 1; i++){
        pathname[i] = strPath[i];
    }
    pathname[strPath.size()] = '\0';

    if (mkdir(pathname, 0777) == -1){
        return pathname;
    }
    else
        cout << "Directory created\n";

    return pathname;
}

#endif