from bs4 import BeautifulSoup
from os.path import exists
from wordfreq import word_frequency
import requests
import re
import json

OUT_FOLDER = 'scraped_sites'

def parse_site(url: str) -> dict[str, str]:
    webpage_response = requests.get(url)
    webpage = webpage_response.content
    soup = BeautifulSoup(webpage, 'html.parser')

    data: dict[str, str] = {}

    html_titles = soup.find_all('h1')
    titles = [item.text.strip('\n').strip(' ') for item in html_titles if item.text != '']
    data['title'] = '\n'.join(titles)

    html_links = soup.find_all('a')
    if html_links:
        links = [item.get('href') for item in html_links]
        link_set = set()
        for link in links:
            if link and 'http' in link:
                link_set.add(link)
        data['links'] = list(link_set)

    # parse paragraph text, which we assume has the main body of the article
    paragraphs = soup.find_all('p')
    text = [item.text for item in paragraphs if item.text != '']
    data['text'] = ' '.join(text)

    return data

def scrape_line(in_data: dict[str, str]) -> dict[str, str]:
    out_data = {
        'date': in_data['Publication Date'],
        'country': in_data['Country'],
        'platform': in_data['Tech Platform'],
        'type': in_data['Product Type'],
        'url': in_data['Link'],
    }

    site_data = parse_site(out_data['url'])
    site_data['ngrams'] = process_ngrams(site_data['text'])
    for key, value in site_data.items():
        out_data[key] = value

    return out_data


def process_ngrams(raw_text: str) -> dict[int, [str, float]]:
    ngrams  = {
        1: {},
        2: {}
    }
    words = raw_text.split(' ')

    for i, word in enumerate(words):
        if word not in ngrams[1]:
            ngrams[1][word] = [1, word_frequency(word, 'en')]
        else:
            ngrams[1][word][0] += 1
        if i==0:
            continue
        bigram =  words[i-1] + ' ' + word
        if bigram not in ngrams[2]:
            bigram_freq = word_frequency(words[i-1], 'en') * word_frequency(word, 'en')
            ngrams[2][bigram] = [1, bigram_freq]
        else:
            ngrams[2][bigram][0] += 1
    return ngrams

class LineProcessor:
    def __init__(self):
        self.entries = {}

    def process_line(self, in_data: dict[str, str]) -> None:
        filename_prefix = in_data['Tech Platform'] + '_' + in_data['Publication Date'].replace('/', '-')

        if filename_prefix not in self.entries:
            self.entries[filename_prefix] = 0
        self.entries[filename_prefix] += 1

        filename = filename_prefix + '_' + str(self.entries[filename_prefix]) + '.json'
        filename_with_path = OUT_FOLDER + '/' + filename

        if not exists(filename_with_path):
            try:
                out_data = scrape_line(in_data)
                with open(filename_with_path, 'w', encoding='utf-8') as f:
                    json.dump(out_data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print("ERROR!", in_data['Link'], e)
