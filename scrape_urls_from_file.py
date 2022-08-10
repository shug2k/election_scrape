import csv

from web_scraper import LineProcessor

FILENAME_WITH_PATH = 'sources/election_history_db.csv'

line_processor = LineProcessor()

with open(FILENAME_WITH_PATH, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        line_processor.process_line(row)
        print(row)
        #print(row['Tech Platform'], row['Publication Date'], row['Country'], row['Product Type'], row['Link'])
