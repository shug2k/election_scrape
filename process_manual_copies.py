import csv

from web_scraper import LineProcessor

FILENAME_WITH_PATH = 'sources/election_history_db.csv'
MANUAL_FILENAME_WITH_PATH = 'sources/manual_url_copies.csv'

url_dict = {}
with open(MANUAL_FILENAME_WITH_PATH, newline='') as manual_csvfile:
    reader = csv.DictReader(manual_csvfile)
    for row in reader:
        url_dict[row["Link"]] = {
            "title": row["Heading"],
            "text": row["Detail"],
        }

line_processor = LineProcessor()

with open(FILENAME_WITH_PATH, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        line_processor.process_line(row, url_dict, False)
        #print(row['Tech Platform'], row['Publication Date'], row['Country'], row['Product Type'], row['Link'])
