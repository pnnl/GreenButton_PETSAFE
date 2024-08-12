from time import perf_counter

from multiprocessing import freeze_support
from config import POWER_DIR, SEED, ENCRYPT, OUTPUT_DIR, YEAR
from list_files import list_files_in_dir
import pandas
import matplotlib.pyplot as plt

# Building module-related imports
from virtual_buildings import meterdata as md

def time_encryption():
    print("Encryption enabled:", str(ENCRYPT))
    files = list_files_in_dir(POWER_DIR)
    start = perf_counter()
    for file in files:
        try:
            file = POWER_DIR + file
            parser = md.MeterDataParser(file, seed=SEED, encrypt=ENCRYPT)
        except Exception as error:
            print("Could not parse files into buildings:", error)
        try:
                parser.output_to_file(OUTPUT_DIR)
                print(file, "done.")
        except Exception as error:
            print("Could not output files:", error)
    end = perf_counter()
    print("Time taken:", end - start, "seconds.")

def main():
    data = {"Encryption": ["No encryption", "Encrypt after aggregation", "Encrypt before aggregation"], \
            "Time to Process (Minutes)": [3.6, 101.2, 1140]}
    frame = pandas.DataFrame(data=data)
    ax = frame.plot.bar(x="Encryption", y="Time to Process (Minutes)", rot=0, figsize=(12, 5), xlabel="", \
                        color=["tab:blue", "tab:blue", "#b36200"])
    ax.bar_label(ax.containers[0], label_type='edge')
    plt.savefig("./time_taken_per_method_" + YEAR + ".png")

    # Benchmarks done on full 2019 data without any prior processing
    # Make sure 2019-encrypted and/or 2019 are not in the output dir
    # for an accurate benchmark
    # Results on 2024-08-02:
    # 216 seconds unencrypted (3.6 min)
    # 6070.44 seconds encrypting after aggregation (101.2 min)
    # Estimated 24 hours encrypting before aggregation

# Thanks, multiprocessing
if __name__ == '__main__':
    freeze_support()
    main()