from Pyfhel import *
import numpy as np
import pandas as pd
import argparse
import os

HE = Pyfhel()           # Creating empty Pyfhel object
ckks_params = {
    'scheme': 'CKKS',   # can also be 'ckks'
    'n': 2**15,         # Polynomial modulus degree. For CKKS, n/2 values can be
                        #  encoded in a single ciphertext. 
                        #  Typ. 2^D for D in [10, 15]
    'scale': 2**30,     # All the encodings will use it for float->fixed point
                        #  conversion: x_fix = round(x_float * scale)
                        #  You can use this as default scale or use a different
                        #  scale on each operation (set in HE.encryptFrac)
    'qi_sizes': [60, 30, 30, 30, 60] # Number of bits of each prime in the chain. 
                        # Intermediate values should be  close to log2(scale)
                        # for each operation, to have small rounding errors.
}
HE.contextGen(**ckks_params)  # Generate context for ckks scheme
HE.keyGen()             # Key Generation: generates a pair of public/secret keys
HE.rotateKeyGen()
NUMBER_OF_DAYS = 45 #Number of days worth of data allowed in a single ciphertext array.

def extractCircuits(df, eeSites, siteID):
    sitePoints = df.loc[df["ee_site_id"]  == int(siteID)]
    #print("Extracting " + str(siteID) + " circuit data.")
    for index, row in sitePoints.iterrows():
        circuitLabel = str(row['circuit_label']).lower()

        if "heat" in circuitLabel:
            eeSites[str(siteID)][str(row["regname"])] = {"circuit_label": circuitLabel}
            eeSites[str(siteID)][str(row["regname"])]["dates"] = {}
            eeSites[str(siteID)][str(row["regname"])]["ciphertexts"] = {}
        elif "mains" in circuitLabel:
            eeSites[str(siteID)]["Mains"] = {"circuit_label": "Mains"}
            eeSites[str(siteID)]["Mains"]["dates"] = {}
            eeSites[str(siteID)]["Mains"]["ciphertexts"] = {}

    if len(eeSites[str(siteID)]) <= 1:
        print(str(siteID) + "\n")       
        print((eeSites[str(siteID)]))
        del eeSites[str(siteID)]


def extractSites(pointsPathname, siteID):
    df = pd.read_csv(pointsPathname)
    eeSites = {}

    if siteID is not None:
        eeSites[str(siteID)] = {}
        extractCircuits(df, eeSites, siteID)
    else:
        sites = df.ee_site_id.unique()
        for site in sites:
            eeSites[str(site)] = {}
            extractCircuits(df, eeSites, site)

    return eeSites


def sumMeasurements(eeSites, arrayLength):
    for site in eeSites:
        for circuit in eeSites[site]:
            for date in eeSites[site][circuit]["dates"]:
                print("Summing measurements for " + str(circuit) + " at " + str(site) + " on " + str(date))
                ctxt = eeSites[site][circuit]["dates"][date]["data"]
                ctxtCopy  = PyCtxt(copy_ctxt = ctxt)
                ctxtCopy2  = PyCtxt(copy_ctxt = ctxt)

                for i in range(arrayLength - 1):
                    ctxtCopy2.__ilshift__(1)
                    ctxtCopy += ctxtCopy2

                eeSites[site][circuit]["dates"][date] = {"sum": ctxtCopy}


def encryptMeasurements(eeSites):
    for site in eeSites:
        for circuit in eeSites[site]:
            dayCounter = 0
            dataArr = []
            startDate = ""

            for date in eeSites[site][circuit]["dates"]:
                if dayCounter == 0:
                    startDate = date

                if dayCounter < NUMBER_OF_DAYS:
                    dataArr += (eeSites[site][circuit]["dates"][date])
                else:
                    circuitNP = np.array(dataArr, dtype=np.float64)
                    ptxt = HE.encodeFrac(circuitNP)
                    print(str(startDate) + " - " + str(date))
                    eeSites[site][circuit]["ciphertexts"][startDate + " - " + date] = HE.encryptPtxt(ptxt)
                    dayCounter = -1
                    dataArr = []

                dayCounter += 1

"""
def encryptMeasurements(date, eeSites, siteID, circuitName, circuitArr):
    circuitNP = np.array(circuitArr, dtype=np.float64)
    ptxt = HE.encodeFrac(circuitNP)   # plaintexts created from arrays shorter than 'n' are filled with zeros.
    eeSites[siteID][circuitName]["dates"] = {date: {"data": HE.encryptPtxt(ptxt)}}
    ptxt = ""
"""

def extractDailyMeasurements(eeSites, datasetPathname):
    df = pd.read_csv(datasetPathname)
    arrayLength = 0
    startTime = df['min_t'].head(1)
    
    for i in startTime:
        date = str(i)
    
    print("Processing data for " + date)
    for site in eeSites:
        siteData = df.loc[df['ee_site_id'] == int(site)]
        for circuit in eeSites[site]:
            circuitData = siteData.loc[siteData['regname'] == str(circuit)]
            circuitArr = []

            for index, row in circuitData.iterrows():
                circuitArr.append(row['power'])
            eeSites[site][circuit]["dates"][date] = circuitArr

            ##encryptMeasurements(date, eeSites, site, circuit, circuitArr)


def extractMeasurements(eeSites, datasetPathname):
    if os.path.isfile(datasetPathname):
        extractDailyMeasurements(eeSites, datasetPathname)
    elif os.path.isdir(datasetPathname):
        fileList = sorted(os.listdir(datasetPathname))

        for file in fileList:
            newPathname = datasetPathname + "/" + file
            extractMeasurements(eeSites, newPathname)


def calculateDailyAverages(eeSites):
    for site in eeSites:
        for circuit in eeSites[site]:
            counter = 1
            for date in eeSites[site][circuit]["dates"]:
                if counter == 1:
                    mainsSumCtxt = eeSites[site]["Mains"]["dates"][date]["sum"]
                    mainsSum = HE.decrypt(mainsSumCtxt)
                    mainsSum = 1 / mainsSum
                    invertedMainsSumCtxt = HE.encrypt(mainsSum)
                    counter = 0

                if circuit != "Mains":
                    percentageOfMain = PyCtxt(copy_ctxt = eeSites[site][circuit]["dates"][date]["sum"])
                    percentageOfMain *= invertedMainsSumCtxt
                    eeSites[site][circuit]["dates"][date]["percentageOfMain"] = percentageOfMain

                    print(str(round(HE.decrypt(percentageOfMain), 3)) + "% of Mains")


parser = argparse.ArgumentParser(prog='main', description='Performs statistics on encrypted data.')
parser.add_argument("-d", "--directory", required=True)
parser.add_argument("-p", "--points", required=True)
parser.add_argument("-s", "--siteID")
args = parser.parse_args()



eeSites = extractSites(args.points, args.siteID)
extractMeasurements(eeSites, args.directory)
encryptMeasurements(eeSites)
print("HE")
#arrayLength = extractDailyMeasurements(eeSites, args.dataset)
#sumMeasurements(eeSites, arrayLength)
#calculateDailyAverages(eeSites)