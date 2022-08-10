# Election Article Scraper

This project scrapes articles about elections, dumps them into a format that can be processed, 
and does some analysis on them (wordclouds, changes in words over time). Files are expected
to be in the format provided in examples in the `sources` directory.

This project requires the packages `beautifulsoup4` and `wordcloud`. You should be able to 
install these with the command `pip install -r requirements.txt` (not tested yet).

## Files
These scripts should be run in order, if doing this from scratch:

`scrape_urls_from_file.py` - script that takes the input file from `sources` and uses BeautifulSoup to pull out article data.
This is then dumped to the directory `scraped_sites` in JSON format.
`process_text.py` - the above format is not great for word clouds, so this script does some cleaning and filtering of words
to make the results more interpretable and faster.
`wordcloud_from_sites.py` - this script generates a word cloud from the `processed_text` directory.