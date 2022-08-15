from bs4 import BeautifulSoup
from os.path import exists
from typing import Optional
import requests
import re
import json

OUT_FOLDER = 'scraped_sites'

class LineProcessor:
    def __init__(self):
        self.entries = {}

    @staticmethod
    def parse_site(url: str) -> dict[str, str]:
        webpage_response = requests.get(url)
        webpage = webpage_response.content
        soup = BeautifulSoup(webpage, 'html.parser')

        data: dict[str, str] = {}

        html_titles = soup.find_all('h1')
        titles = [item.text.strip('\n').strip(' ') for item in html_titles if item.text != '']
        data['title'] = '\n'.join(titles)
        #print(data['title'])

        html_links = soup.find_all('a')
        if html_links:
            links = [item.get('href') for item in html_links]
            link_set = set()
            for link in links:
                if link and 'http' in link:
                    link_set.add(link)
            data['links'] = list(link_set)
        #print(data['links'])

        # parse paragraph text, which we assume has the main body of the article
        paragraphs = soup.find_all('p')
        text = [item.text for item in paragraphs if item.text != '']
        data['text'] = ' '.join(text)
        #print(data['text'])

        return data

    @staticmethod
    def get_metadata_from_line(in_data: dict[str, str]) -> dict[str, str]:
        return {
            'date': in_data['Publication Date'],
            'country': in_data['Country'],
            'platform': in_data['Tech Platform'],
            'type': in_data['Product Type'],
            'url': in_data['Link'],
        }

    @staticmethod
    def scrape_line(in_data: dict[str, str]) -> dict[str, str]:
        out_data = LineProcessor.get_metadata_from_line(in_data)

        site_data = LineProcessor.parse_site(out_data['url'])
        for key, value in site_data.items():
            out_data[key] = value
        #print(out_data)

        return out_data

    def process_line(self, in_data: dict[str, str], manual_data: dict[str, dict[str, str]] = {}, scrape_data: bool = True) -> str:
        filename_prefix = in_data['Tech Platform'] + '_' + in_data['Publication Date'].replace('/', '-')

        if filename_prefix not in self.entries:
            self.entries[filename_prefix] = 0
        self.entries[filename_prefix] += 1

        filename = filename_prefix + '_' + str(self.entries[filename_prefix]) + '.json'
        filename_with_path = OUT_FOLDER + '/' + filename

        if not exists(filename_with_path) or in_data['Link'] in manual_data:
            try:
                out_data = None
                if in_data['Link'] in manual_data:
                    out_data = LineProcessor.get_metadata_from_line(in_data)
                    out_data['title'] = manual_data[in_data['Link']]['title']
                    out_data['text'] = manual_data[in_data['Link']]['text']
                elif scrape_data is True:
                    out_data = LineProcessor.scrape_line(in_data)

                if out_data:
                    print(in_data)
                    with open(filename_with_path, 'w', encoding='utf-8') as f:
                        json.dump(out_data, f, ensure_ascii=False, indent=4)

            except Exception as e:
                print("ERROR!", in_data['Link'], e)

        return filename_with_path

    def process_line_with_manual_copy(self, in_data: dict[str, str]) -> None:
        filename_prefix = in_data['Tech Platform'] + '_' + in_data['Publication Date'].replace('/', '-')

        if filename_prefix not in self.entries:
            self.entries[filename_prefix] = 0
        self.entries[filename_prefix] += 1

        filename = filename_prefix + '_manual_' + str(self.entries[filename_prefix]) + '.json'
        filename_with_path = OUT_FOLDER + '/' + filename

        if not exists(filename_with_path):
            try:
                out_data = LineProcessor.scrape_line(in_data)
                with open(filename_with_path, 'w', encoding='utf-8') as f:
                    json.dump(out_data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print("ERROR!", in_data['Link'], e)
