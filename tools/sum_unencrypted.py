import pandas

def sum_unencrypted(FILE):
    with open(FILE, "r") as csv_file:
        file_contents = pandas.read_csv(csv_file)
    file_contents = file_contents[file_contents["regname"] == "Mains"]

    power_sum = file_contents["power"].sum()
    return power_sum