import json
import os
import re

SOURCE_FOLDER = 'scraped_sites'
DESTINATION_FOLDER = 'processed_text'

for filename in os.listdir(SOURCE_FOLDER):
    filename_with_path = SOURCE_FOLDER + '/' + filename

    out_file_with_path = DESTINATION_FOLDER + '/' + filename.strip('json') + 'txt'

    with open(filename_with_path) as f:
        data = json.load(f)
        if 'pdf' not in data['url']:
            text = data['text']

            words = re.findall(r'\w+', text.lower())
            words = [word for word in words if len(word) > 2]

            out_handler = open(out_file_with_path, 'w')
            out_handler.write(' '.join(words))
            out_handler.close()

