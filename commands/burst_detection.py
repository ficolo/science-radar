import pandas as pd
import numpy as np

from collections import Counter
from itertools import dropwhile

from burst_detection import *

import seaborn as sns
import matplotlib.pyplot as plt

blog_blue = '#64C0C0'
blue_cmap = sns.light_palette(blog_blue, as_cmap=True)
red_cmap = sns.light_palette('#e43d00', as_cmap=True)
stopwords = [
    'OURSELVES', 'HERS', 'BETWEEN', 'YOURSELF', 'BUT', 'AGAIN', 'THERE', 'ABOUT', 'ONCE', 'DURING', 'OUT', 'VERY',
    'HAVING', 'WITH', 'THEY', 'OWN', 'AN', 'BE', 'SOME', 'FOR', 'DO', 'ITS', 'YOURS', 'SUCH', 'INTO', 'OF', 'MOST',
    'ITSELF', 'OTHER', 'OFF', 'IS', 'S', 'AM', 'OR', 'WHO', 'AS', 'FROM', 'HIM', 'EACH', 'THE', 'THEMSELVES', 'UNTIL',
    'BELOW', 'ARE', 'WE', 'THESE', 'YOUR', 'HIS', 'THROUGH', 'DON', 'NOR', 'ME', 'WERE', 'HER', 'MORE', 'HIMSELF',
    'THIS', 'DOWN', 'SHOULD', 'OUR', 'THEIR', 'WHILE', 'ABOVE', 'BOTH', 'UP', 'TO', 'OURS', 'HAD', 'SHE', 'ALL', 'NO',
    'WHEN', 'AT', 'ANY', 'BEFORE', 'THEM', 'SAME', 'AND', 'BEEN', 'HAVE', 'IN', 'WILL', 'ON', 'DOES', 'YOURSELVES',
    'THEN', 'THAT', 'BECAUSE', 'WHAT', 'OVER', 'WHY', 'SO', 'CAN', 'DID', 'NOT', 'NOW', 'UNDER', 'HE', 'YOU', 'HERSELF',
    'HAS', 'JUST', 'WHERE', 'TOO', 'ONLY', 'MYSELF', 'WHICH', 'THOSE', 'I', 'AFTER', 'FEW', 'WHOM', 'T', 'BEING', 'IF',
    'THEIRS', 'MY', 'AGAINST', 'A', 'BY', 'DOING', 'IT', 'HOW', 'FURTHER', 'WAS', 'HERE', 'THAN', 'ARTICLE', 'PUBLIC',
    'GROUP', 'JOURNAL', 'OPEN', 'ACCESS', 'AUTHOR', 'PUBLICATION', 'LICENSE'
]


def pre_processing(publications):
    dates = set()
    words = set()
    for publication in publications:
        dates.add(publication.date[:7])
        words = words.union(set(publication.annotations))
    dates = list(dates)
    words = list(words)
    word_fqs = {}
    total = [0 for date in dates]
    for word in words:
        word_fqs[word] = []
        for date in dates:
            word_fqs[word].append(0)
        for publication in publications:
            if word in publication.annotations:
                word_fqs[word][dates.index(publication.date[:7])] += 1
                total[dates.index(publication.date[:7])] += 1
    return word_fqs, total, len(dates)


def get_word_burst(file_name, cols, word_col, plain_text=False, separator='|', dataset_name='dataset'):
    data = pd.read_csv(file_name, usecols=cols, index_col=False)
    if plain_text:
        data['annotations'] = data[word_col].apply(lambda x: x.upper().replace(',', ' ').replace('.', ' ').split())
    else:
        data['annotations'] = data[word_col].apply(lambda x: x.split(separator))
    data['date'] = data['date'].apply(lambda x: x.split('T')[0])
    data['publication_year'] = data['date'].apply(lambda x: x.split('-')[0])
    data['publication_month'] = data['date'].apply(lambda x: x.split('-')[1])
    year_column = data['publication_year'].astype(int)
    min_year = year_column.min()
    max_year = year_column.max()
    print(min_year, max_year)
    print('Number of rows in dataset: ', len(data))
    word_counts = Counter(data['annotations'].apply(pd.Series).stack())
    print('Number of unique words: ', len(word_counts))
    count_threshold = 1000

    for key, count in dropwhile(lambda x: x[1] >= count_threshold, word_counts.most_common()):
        del word_counts[key]
    word_counts = {k: v for k, v in word_counts.items() if k not in stopwords}
    print('Number of unique words with at least', count_threshold, 'occurrences: ', len(word_counts))
    unique_words = list(word_counts.keys())
    d = data.groupby(['publication_year', 'publication_month'])['annotations'].count().reset_index(drop=True)
    # # plot the number of articles published each month#plot t
    #
    # # initialize a figure
    # plt.figure(figsize=(10, 5))
    # # create a color map
    # # plot bars
    # # axes = plt.bar(d.index, d, width=1, color=blue_cmap((d-np.min(d))/(np.max(d)-np.min(d)))) #color according to height
    # axes = plt.bar(d.index, d, width=1, color=blue_cmap(d.index.values / d.index.max()))  # color according to month
    # print(d.index)
    # # format plot
    # plt.grid(axis='y')
    # plt.xlim(0, len(d))
    # labels = [str(int(min_year + (month / 12))) if month % 12 == 0 else calendar.month_name[(month % 12) + 1] for month in range(0, (max_year-min_year)*12, 1)]
    # plt.xticks(range(0, len(d), 1), labels, rotation='vertical')
    # plt.tick_params(axis='x', length=max_year - min_year)
    # plt.title('Number of {} related articles published each month'.format(dataset_name))
    # sns.despine(left=True)
    #
    # plt.tight_layout()
    # plt.savefig('{}_articles_published_over_time.png'.format(dataset_name), dpi=300)
    # plt.show()

    # create a dataframe to contain all target word propotions
    all_r = pd.DataFrame(columns=unique_words, index=d.index)
    print(all_r)

    # usually it's better (faster) to create a document x unique_word dataframe
    # that indicates if the word is in the document all in one step, and then
    # use groupby to sum the counts for each time period. However, I kept getting
    # a dead kernel and I think the issue was that there wasn't enough memory to
    # store the document x word dataframe.
    for i, word in enumerate(unique_words):

        all_r[word] = pd.concat([data.loc[:, ['publication_year', 'publication_month']],
                                 data['annotations'].apply(lambda x: word in x)],
                                axis=1) \
            .groupby(by=['publication_year', 'publication_month']) \
            .sum() \
            .reset_index(drop=True)

        # print out a status indicator
        if np.mod(i, 100) == 0:
            print('word', i, 'complete')
    all_bursts = pd.DataFrame(columns=['begin', 'end', 'weight'])

    # define variables
    s = 2  # resolution of state jumps; higher s --> fewer but stronger bursts
    gam = 0.5  # difficulty of moving up a state; larger gamma --> harder to move up states, less bursty
    n = len(d)  # number of timepoints

    # loop through unique words
    for i, word in enumerate(unique_words):

        r = all_r.loc[:, word].astype(int)

        # find the optimal state sequence (using the Viterbi algorithm)
        [q, d, r, p] = burst_detection(r, d, n, s, gam, smooth_win=5)

        # enumerate the bursts
        bursts = enumerate_bursts(q, word)

        # find weight of each burst
        bursts = burst_weights(bursts, r, d, p)

        # add the bursts to a list of all bursts
        all_bursts = all_bursts.append(bursts, ignore_index=True)

        # print a progress report every 100 words
        if np.mod(i, 100) == 0:
            print('word', i, 'complete')
    all_bursts['weight'] = (all_bursts['weight'] - all_bursts['weight'].min()) / all_bursts['weight'].max()
    all_bursts.sort_values(by='weight', ascending=False)

    # save bursts to an excel file
    #all_bursts.to_excel('{}_2010_2018_{}.xlsx'.format(dataset_name, word_col))
    n_bursts = 100
    top_bursts = all_bursts.sort_values(by='weight', ascending=False).reset_index(drop=True).loc[:n_bursts, :]
    # sort bursts by end date
    sorted_bursts = top_bursts.sort_values('end', ascending=False).reset_index(drop=True)
    # for bursts that end at the last timepoint, sort by start point
    last_timepoint = np.max(sorted_bursts['end'])
    sorted_bursts.loc[sorted_bursts['end'] == last_timepoint, :] = sorted_bursts.loc[
                                                                   sorted_bursts['end'] == last_timepoint, :] \
        .sort_values(by='begin', ascending=False) \
        .reset_index(drop=True)

    # format bars
    bar_width = 0.8  # width of bars
    bar_pos = np.array(range(len(sorted_bursts)))  # positions of top edge of bars
    ylabel_pos = bar_pos + (bar_width / 2)  # y axis label positions
    n = len(d)  # number of time points

    # initialize the matplotlib figure
    f, ax = plt.subplots(figsize=(10, 25))

    # plot current bursts in blue and old bursts in gray
    sorted_bursts['color'] = sorted_bursts['weight'].apply(lambda weight: red_cmap(weight))  # gray
    # sorted_bursts.loc[sorted_bursts['end'] == last_timepoint, 'color'] = blog_blue

    # plot the end points
    end_bars = ax.barh(bar_pos, sorted_bursts.loc[:, 'end'], bar_width, align='edge',
                       color=sorted_bursts['color'], edgecolor='none')

    # plot the start points (in white to blend in with the background)
    start_bars = ax.barh(bar_pos, sorted_bursts.loc[:, 'begin'], bar_width, align='edge',
                         color='w', edgecolor='none')

    # label each burst
    plt.yticks(ylabel_pos, '')  # remove default labels
    for burst in range(len(sorted_bursts)):
        width = int(end_bars[burst].get_width())
        # place label on right side for early bursts
        if width <= (n / 2):
            plt.text(width + 4, ylabel_pos[burst], sorted_bursts.loc[burst, 'label'],
                     fontsize=12, va='center')
        # place label on left side for late bursts
        else:
            width = int(start_bars[burst].get_width())
            plt.text(width - 4, ylabel_pos[burst], sorted_bursts.loc[burst, 'label'],
                     fontsize=12, va='center', ha='right')

    # format plot
    ax.set(xlim=(0, n), ylim=(0, n_bursts + 1), ylabel='', xlabel='')
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_color([0.9, 0.9, 0.9])
    ax.spines["right"].set_color([0.9, 0.9, 0.9])
    for x in range(0, n):
        if x % 12 == 0:
            plt.axvline(x, color='green', linestyle='-', linewidth=0.8, alpha=0.25)
        else:
            plt.axvline(x, color='green', linestyle='dotted', linewidth=0.4, alpha=0.25)
    labels = ['{}-{}'.format(date[0], date[1]) for date in
              data.groupby(['publication_year', 'publication_month'])['annotations'].count().index]
    print(labels)
    plt.xticks(range(0, n, 1), labels, rotation='vertical')

    ax.set_title(
        'Timeline of the top ' + str(n_bursts) + ' "bursting" topics in the {} literature'.format(dataset_name),
        size=14)
    plt.tight_layout()
    #plt.savefig("{}_{}_bursts_top100_g0-5_s2.png".format(dataset_name, word_col), bbox_inches="tight", dpi=300)
    plt.show()


def plot_most_common_words(word_counts, n, title, gradient, label_type):
    # remove words that relate to MRI and non-content words (like articles and prepositions)
    discard_words = ['of', 'in', 'and', 'the', 'a', 'with', 'for', 'to', 'on', 'an', 'by', 'using',
                     'from', 'as', 'is', 'at', 'between', 'during',
                     'mr', 'fmri', 'magnetic', 'resonance', 'imaging', 'mri']
    for key in discard_words:
        del word_counts[key]
    word_counts = pd.DataFrame(word_counts.most_common()[:n], columns=['word', 'count'])

    # define colors for bars
    if gradient:
        bar_colors = blue_cmap((word_counts['count']) / (word_counts['count'].max()))
    else:
        bar_colors = blog_blue

    # create a horizontal bar plot
    plt.barh(range(n, 0, -1), word_counts['count'], height=0.85, color=bar_colors, alpha=1)

    # format plot
    sns.despine(left=True, bottom=True)
    plt.ylim(0, n + 1)
    plt.title(title)
    plt.grid(axis='x')

    # label bars
    if label_type == 'counts':
        plt.yticks(range(n, 0, -1), word_counts['word']);
        for i, row in word_counts.iterrows():
            plt.text(row['count'] - 100, 50 - i - 0.2, row['count'], horizontalalignment='right', fontsize='12',
                     color='white')

    elif label_type == 'labeled_bars_left':
        plt.yticks(range(n, 0, -1), [])
        for i, row in word_counts.iterrows():
            plt.text(50, n - i - 0.2, row['word'], horizontalalignment='left', fontsize='14')

    elif label_type == 'labeled_bars_right':
        plt.yticks(range(n, 0, -1), [])
        for i, row in word_counts.iterrows():
            plt.text(row['count'], n - i - 0.2, row['word'], horizontalalignment='right', fontsize='14')

    else:
        plt.yticks(range(n, 0, -1), word_counts['word'])

# get_word_burst('../data/zika_annotations.csv', ['id', 'date', 'annotations'], 'annotations', dataset_name='Zika')
# get_word_burst('../data/zika_fulltext.csv', ['title', 'date', 'fullText'], 'fullText', dataset_name='Zika', plain_text=True)
