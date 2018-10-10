import pandas as pd


def get_co_authorship(csv_file_path, year):
    data = pd.read_csv(csv_file_path, usecols=['id', 'date', 'authors'], index_col=False)
    data['publication_year'] = data['date'].apply(lambda x: x.split('-')[0])
    data['publication_month'] = data['date'].apply(lambda x: x.split('-')[1])
    return