from Pyfhel import *
import numpy as np
import pandas as pd
import argparse
import os
from datetime import datetime, date, timedelta

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

#print(HE.sizeof_public_key())
#print(HE.sizeof_secret_key())

##################################################################################
# THESE CONSTANTS WILL BE SUPPLIED OR CALCULATED LATER IN THE PROGRAMS LIFECYCLE #
##################################################################################
NUMBER_OF_DAYS = 30 #Number of days worth of data allowed in a single ciphertext array.
NUMBER_OF_DATAPOINTS = 96 #Number of data points in the CSV file.


def extractCircuits(df, eeSites, siteID):
    """
    Extracts the electrical circuits that contain the string "heat" or "mains" anywhere in the circuit label.
    Empty dictionaries for "dateRanges" for the electrical circuits are initialized.
    
    :param df: A Pandas dataframe obtained from reading a CSV file containing data about electrical circuits.
    :type df: Pandas.DataFrame
    :param eeSites: A dictionary containing data about the electrical circuits. The siteID is used as the keys.
    :type eeSites: dict
    :param siteID: The ID of the site to extract the electrical circuit data from.
    :type siteID: str
    """

    sitePoints = df.loc[df["ee_site_id"]  == int(siteID)]
    print("Extracting " + str(siteID) + " circuit data.")

    for index, row in sitePoints.iterrows():
        circuitLabel = str(row['circuit_label']).lower()

        if "heat" in circuitLabel:
            eeSites[str(siteID)][str(row["regname"])] = {"circuit_label": circuitLabel}
            eeSites[str(siteID)][str(row["regname"])]["dateRanges"] = {}
        elif "mains" in circuitLabel:
            eeSites[str(siteID)]["Mains"] = {"circuit_label": "Mains"}
            eeSites[str(siteID)]["Mains"]["dateRanges"] = {}

    if len(eeSites[str(siteID)]) <= 1:
        print(str(siteID) + "\n")       
        print((eeSites[str(siteID)]))
        del eeSites[str(siteID)]


def extractSites(pointsPathname, siteID):
    """
    Reads the CSV file with the given pathname in ``pointsPathname`` to obtain information about 
    the electrical circuits at the site(s). If a siteID is not provided, all electrical circuit data
    from all sites are obtained from the CSV file.

    :param pointsPathname: The pathname to the file containing information about the circuits at
                           each site.
    :type pointsPathname: str
    :param siteID: The ID of the site to extract information about.
    :type siteID: str or None

    :return: A dictionary containing information about all electrical circuits at the site(s).
    :rtype: dict
    """
    
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


def sumMeasurements(eeSites):
    for site in eeSites:
        for circuit in eeSites[site]:
            for dateRange in eeSites[site][circuit]["dateRanges"]:
                originalCtxt = eeSites[site][circuit]["dateRanges"][dateRange]["ciphertext"]
                ctxtCopy = PyCtxt(copy_ctxt = originalCtxt)
                ctxtCopy2 = PyCtxt(copy_ctxt = originalCtxt)

                #[1, 2, 3]
                #[2, 3, 1]

                #[3, 5, 4]
                #[3, 2, 1]

                #[6, 7, 5]

                for i in range(NUMBER_OF_DATAPOINTS):
                    ctxtCopy2.__ilshift__(1)
                    ctxtCopy += ctxtCopy2

                eeSites[site][circuit]["dateRanges"][dateRange]["sum"] = ctxtCopy

                if circuit == "Mains":
                    mainsSum = HE.decrypt(ctxtCopy)
                    mainsSum = 1 / mainsSum
                    circuitNP = np.array(mainsSum, dtype=np.float64)
                    ptxt = HE.encodeFrac(circuitNP)
                    eeSites[site]["Mains"]["dateRanges"][dateRange]["invertedSum"] = HE.encrypt(ptxt)


def encryptMeasurements(eeSites):
    """
    Each electrical circuits data for the different date ranges are encrypted.

    :param eeSites: A dictionary containing data about the electrical circuits. The siteID is used as the keys.
    :type eeSites: dict
    """

    for site in eeSites:
        for circuit in eeSites[site]:
            for range in eeSites[site][circuit]["dateRanges"]:
                dateRangeData = eeSites[site][circuit]["dateRanges"][range]
                circuitNP = np.array(dateRangeData, dtype=np.float64)
                ptxt = HE.encodeFrac(circuitNP)
                eeSites[site][circuit]["dateRanges"][range] = {"ciphertext": HE.encrypt(ptxt),
                                                               "sum": "",
                                                               "invertedSum": ""
                                                               }
                

def extractMultipleMeasurements(eeSites, datasetPathname):
    """
    Reads and extracts data from all the CSV files in the directory at ``datasetPathname``.
    The data is stored in the eeSites dictionary.
    
    :param eeSites: A dictionary containing data about the electrical circuits. The siteID is used as the keys.
    :type eeSites: dict
    :param datasetPathname: The pathname to a directory containing multiple CSV files.
    :type datasetPathname: str
    """

    fileList = sorted(os.listdir(datasetPathname))
    counter = 0
    startDate = ""
    endDate = ""

    for file in fileList:
        newPathname = datasetPathname + "/" + file
        df = pd.read_csv(newPathname)
        print("Processing data for " + str(df['min_t'].head(1)) + ".")

        if counter == NUMBER_OF_DAYS:
            startDate = ""
            endDate = ""
            counter = 0

        if counter == 0:
            start = df['min_t'].head(1)

            for i in start:
                startDate = str(i)

            end = datetime.strptime(startDate, "%Y-%m-%d")
            end += timedelta(NUMBER_OF_DAYS - 1)
            endDate = datetime.strftime(end, "%Y-%m-%d")
            
        for site in eeSites:
            siteData = df.loc[df['ee_site_id'] == int(site)]

            for circuit in eeSites[site]:
                circuitData = siteData.loc[siteData['regname'] == str(circuit)]
                circuitArr = []

                print(circuit)
                for index, row in circuitData.iterrows():
                    if circuit == "Mains":
                        try:
                            circuitArr.append(1 / row['power'])
                        except:
                            circuitArr.append(0.0)
                    else:       
                        circuitArr.append(row['power'])
                    
                if counter == 0:
                    eeSites[site][circuit]["dateRanges"][startDate + " - " + endDate] = circuitArr
                else:
                    for entry in circuitArr:
                        eeSites[site][circuit]["dateRanges"][startDate + " - " + endDate].append(entry)
                    
        counter += 1


def extractDailyMeasurements(eeSites, datasetPathname):
    """
    Reads and extracts data from a CSV containing a single day's worth of electrical circuit measurement data.
    The data is stored in the eeSites dictionary.
    
    :param eeSites: A dictionary containing data about the electrical circuits. The siteID is used as the keys.
    :type eeSites: dict
    :param datasetPathname: The pathname to a CSV file containing a single day's worth of data.
    :type datasetPathname: str
    """

    df = pd.read_csv(datasetPathname)
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
            
            #[0.1, 0.2, 0.3]
            #eeSites {491: {CIRCUIT_1: {"dateRanges": "09-18-2024": [0.1, 0.2, 0.3]} }}
            eeSites[site][circuit]["dateRanges"][date] = circuitArr



def calculateAverages(eeSites):
    for site in eeSites:
        for circuit in eeSites[site]:
            if circuit != "Mains":
                for dateRange in eeSites[site][circuit]["dateRanges"]:
                    invMainsCtxt = eeSites[site]["Mains"]["dateRanges"][dateRange]["invertedSum"]
                    circuitCtxt = eeSites[site][circuit]["dateRanges"][dateRange]["sum"]
                    averageCtxt = PyCtxt(copy_ctxt = circuitCtxt)
                    


def calculateDailyAverages(eeSites):
    for site in eeSites:
        for circuit in eeSites[site]:
            counter = 1
            for date in eeSites[site][circuit]["dateRanges"]:
                if counter == 1:
                    mainsSumCtxt = eeSites[site]["Mains"]["dateRanges"][date]["sum"]
                    mainsSum = HE.decrypt(mainsSumCtxt)
                    mainsSum = 1 / mainsSum
                    invertedMainsSumCtxt = HE.encrypt(mainsSum)
                    counter = 0

                if circuit != "Mains":
                    percentageOfMain = PyCtxt(copy_ctxt = eeSites[site][circuit]["dateRanges"][date]["sum"])
                    percentageOfMain *= invertedMainsSumCtxt
                    eeSites[site][circuit]["dateRanges"][date]["percentageOfMain"] = percentageOfMain

                    print(str((HE.decrypt(percentageOfMain)[0]) * 100) + "% of Mains")


def main():
    parser = argparse.ArgumentParser(prog='main', description='Performs statistics on encrypted data.')
    parser.add_argument("-d", "--directory", required=True)
    parser.add_argument("-p", "--points", required=True)
    parser.add_argument("-s", "--siteID")
    args = parser.parse_args()

    arr = [0]*512
    circuitNP = np.array(arr, dtype=np.float64)
    ptxt = HE.encodeFrac(circuitNP)

    eeSites = extractSites(args.points, args.siteID)
    """
    -------------------------
    eeSites Dictionary Format
    -------------------------

    eeSites: {
        EE_SITE_ID: {
            REGNAME (example-CIRCUIT_1): {
                "circuit_label": (Example: Water Heater),
                "dateRanges": {
                    (Example: 2024-01-01 - 2024-01-11): {
                        "ciphertext": Ctxt ciphertext of the data from that range.,
                        "sum": Ctxt ciphertext containing the sums of each date.,
                        "invertedSum": Ctxt
                        }
                    }
                }
            }
    """

    if os.path.isfile(args.directory):
        extractDailyMeasurements(eeSites, args.directory)
    elif os.path.isdir(args.directory):
        extractMultipleMeasurements(eeSites, args.directory)

    encryptMeasurements(eeSites)
    sumMeasurements(eeSites)
    #calculateAverages(eeSites)
    #arrayLength = extractDailyMeasurements(eeSites, args.dataset)
    #sumMeasurements(eeSites, arrayLength)
    calculateDailyAverages(eeSites)


if __name__ == '__main__':
    main()