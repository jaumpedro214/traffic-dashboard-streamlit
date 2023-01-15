import os

URL = "http://servicosbhtrans.pbh.gov.br/Bhtrans/webservice/{}_{}.zip"
MONTHS = ["JANEIRO", "FEVEREIRO", "MARÇO"]
YEARS = [2022]


if __name__ == "__main__":
    for year in YEARS:
        for month in MONTHS:
            url = URL.format(month, year)
            print(f"Downloading {month} {year}...")
            os.system(f"wget {url}")
            print(f"Unzipping {month} {year}...")
            os.system(f"unzip {month}_{year}.zip")
            print(f"Removing {month} {year}...")
            os.system(f"rm {month}_{year}.zip")