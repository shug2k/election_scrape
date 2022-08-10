import json
import os
import matplotlib.pyplot as plt
from wordcloud import WordCloud

SOURCE_FOLDER = 'processed_text'

all_text = ''
count = 0
for filename in os.listdir(SOURCE_FOLDER):
    filename_with_path = SOURCE_FOLDER + '/' + filename

    with open(filename_with_path) as f:
        text = f.read()
        all_text += ' ' + text

wordcloud = WordCloud(width=4000, height=3200).generate(all_text)

plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.show()


