import os
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS

SOURCE_FOLDER = 'processed_text'

stopwords = set(STOPWORDS)
election_stopwords_filename = 'sources/election_stopwords.txt'

with open(election_stopwords_filename) as f_stopwords:
    for line in f_stopwords:
        stopwords.add(line.strip('\n'))

all_text = ''
for filename in os.listdir(SOURCE_FOLDER):
    if filename[0] == '.':
        continue

    filename_with_path = SOURCE_FOLDER + '/' + filename

    with open(filename_with_path) as f:
        text = f.read()
        all_text += ' ' + text

wordcloud = WordCloud(width=1000, height=800, stopwords=stopwords).generate(all_text)

plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.savefig(fname='wordclouds/overall.png', dpi=600)
plt.show()
