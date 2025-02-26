import pandas
from config import FILE

def count_sites(FILE):
    with open(FILE, "r") as csv_file:
        frame = pandas.read_csv(csv_file)
    site_ids = pandas.unique(frame["ee_site_id"])
    site_id_count = len(site_ids)
    return(site_id_count)

print(count_sites(FILE))