from utils import mongodb_access
import json


def month_year_iter(start_month, start_year, end_month, end_year):
    ym_start = 12 * start_year + start_month - 1
    ym_end = 12 * end_year + end_month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m + 1


def get_statistics():
    papers_by_month = mongodb_access.get_paper_by_month('publications', 'zika', 'localhost', 27017)
    authors_by_month = mongodb_access.get_unique_authors_by_month('publications', 'zika', 'localhost', 27017)
    references_by_month = mongodb_access.get_unique_references_by_month('publications', 'zika', 'localhost', 27017)
    keywords_by_month = mongodb_access.get_unique_keywords_by_month('publications', 'zika', 'localhost', 27017)
    statistics = dict(series=[], labels=[])
    statistics['series'].append(dict(name='# Papers', data=[]))
    statistics['series'].append(dict(name='# Unique Authors', data=[]))
    statistics['series'].append(dict(name='# References/10', data=[]))
    statistics['series'].append(dict(name='# Keywords', data=[]))
    for year, month in month_year_iter(1, 2010, 1, 2018):
        month = str(month) if month > 9 else '0' + str(month)
        label = '{}-{}'.format(year, month)
        statistics['labels'].append(label)
        statistics['series'][0]['data'].append(papers_by_month[label] if label in papers_by_month else None)
        statistics['series'][1]['data'].append(authors_by_month[label] if label in authors_by_month else None)
        statistics['series'][2]['data'].append(references_by_month[label]/10 if label in references_by_month else None)
        statistics['series'][3]['data'].append(keywords_by_month[label] if label in keywords_by_month else None)
    return statistics


def get_basic_stats(database, collection, host, port, start_year, start_month, end_year, end_month):
    basic_stats = dict()
    basic_stats['papersCount'] = mongodb_access.get_paper_count(database, collection, host, port, start_year, start_month, end_year, end_month)
    basic_stats['authorsCount'] = mongodb_access.get_authors_count(database, collection, host, port, start_year, start_month, end_year, end_month)
    basic_stats['referencesCount'] = mongodb_access.get_references_count(database, collection, host, port, start_year, start_month, end_year, end_month)
    basic_stats['keywordsCount'] = mongodb_access.get_keywords_count(database, collection, host, port, start_year, start_month, end_year, end_month)
    return basic_stats


#print(get_basic_stats('publications', 'zika', 'localhost', 27017, 2010, 1, 2018, 1))
print(mongodb_access.get_top_terms('publications', 'zika', 'localhost', 27017, 2010, 1, 2018, 1))










