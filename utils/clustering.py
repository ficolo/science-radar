from utils.mongodb_access import get_references_annotations, get_references_count
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from time import time
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets.samples_generator import make_blobs
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram
from itertools import cycle, islice
from scipy.cluster import hierarchy
import seaborn as sns
from sklearn.metrics.pairwise import cosine_similarity

sns.set(color_codes=True)


def get_feature_matrix(documents, all_terms):
    observations = []
    article_index = []
    for document in documents:
        label = document['_id']
        article_index.append(dict(id=label, title=document['_id']))
        feature_vector = []
        for term in all_terms:
            if term in document['annotations']:
                feature_vector.append(1.0)
            else:
                feature_vector.append(0.0)
        observations.append(feature_vector)
    return article_index, observations


def plot_dendrogram(model, **kwargs):

    # Children of hierarchical clustering
    children = model.children_

    # Distances between each pair of children
    # Since we don't have this information, we can use a uniform one for plotting
    distance = np.arange(children.shape[0])

    # The number of observations contained in each cluster level
    no_of_observations = np.arange(2, children.shape[0]+2)

    # Create linkage matrix and then plot the dendrogram
    linkage_matrix = np.column_stack([children, distance, no_of_observations]).astype(float)

    # Plot the corresponding dendrogram
    dendrogram(linkage_matrix, **kwargs)


def get_clusters(database, collection, mongo_host, mongo_port, start_year, start_month, end_year, end_month):
    print('Getting terms for {}-{} to {}-{}'.format(start_year, start_month, end_year, end_month))
    references, index = get_references_annotations(database, collection, mongo_host, mongo_port, start_year, start_month, end_year, end_month)
    print('Got {}'.format(len(references)))
    t0 = time()
    print('vectorizing')
    vectorizer = TfidfVectorizer(use_idf=True)
    try:
        X = vectorizer.fit_transform(references)
    except:
        return 0, {}
    print(vectorizer.get_feature_names())
    print("n_samples: %d, n_features: %d" % X.shape)
    #############################################################################
    # Compute DBSCAN
    db = DBSCAN(metric='cosine', eps=0.5).fit(X)
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_

    # Number of clusters in labels, ignoring noise if present.
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    unique_labels = set(labels)
    colors = [plt.cm.Spectral(each)
              for each in np.linspace(0, 1, len(unique_labels))]
    y_pred = labels.astype(np.int)
    number_of_clusters = len(unique_labels)
    grouped_ids = dict()
    for i, label in enumerate(labels):
        if label == -1:
            continue
        if label not in grouped_ids:
            grouped_ids[label] = []
        grouped_ids[label].append(index[i])
    return number_of_clusters, grouped_ids


def get_clusters_range(database, collection, mongo_host, mongo_port, start_year, start_month, end_year, end_month):
    cluster_numbers = dict()
    for year, month in month_year_iter(start_month, start_year, end_month, end_year):
        cluster_number, clusters = get_clusters(database, collection, mongo_host, mongo_port, start_year, start_month, year, month)
        cluster_numbers['{}-{}'.format(year, month)] = cluster_number
    return cluster_numbers


def month_year_iter(start_month, start_year, end_month, end_year):
    ym_start = 12 * start_year + start_month - 1
    ym_end = 12 * end_year + end_month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m + 1


#print(get_clusters_range('publications', 'zika', 'localhost', 27017, 2010, 1, 2018, 1))

# print('Getting terms')
# references, index = get_references_annotations('publications', 'zika', 'localhost', 27017, 2010, 1, 2014, 12)
# # most_cited = get_references_count('publications', 'zika', 'localhost', 27017, 2010, 1, 2014, 12)
# # to_cluster = []
# # for i, pmid in enumerate(index):
# #     if pmid in most_cited:
# #         to_cluster.append(references[i])
# t0 = time()
# print('vectorizing')
# vectorizer = TfidfVectorizer(use_idf=True)
# X = vectorizer.fit_transform(references)
# print(vectorizer.get_feature_names())
# print("n_samples: %d, n_features: %d" % X.shape)
# #############################################################################
# #Compute DBSCAN
# db = DBSCAN(metric='cosine', eps=0.5).fit(X)
# core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
# core_samples_mask[db.core_sample_indices_] = True
# labels = db.labels_
#
# # Number of clusters in labels, ignoring noise if present.
# n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
# unique_labels = set(labels)
# colors = [plt.cm.Spectral(each)
#           for each in np.linspace(0, 1, len(unique_labels))]
# y_pred = labels.astype(np.int)
# print(len(unique_labels))
# grouped_ids = dict()
# for i, label in enumerate(labels):
#     if label == -1:
#         continue
#     if label not in grouped_ids:
#         grouped_ids[label] = []
#     grouped_ids[label].append(index[i])
# print(grouped_ids)
# similarities = cosine_similarity(X.todense())
# print(X.todense())
# clusters = hierarchy.linkage(X.todense(), metric="cosine")
# g = sns.clustermap(similarities, row_linkage=clusters, col_linkage=clusters, xticklabels=False, yticklabels=False)
# #ax = sns.heatmap(similarities)
# plt.show()
# X = X.todense()
# threshold = 0.5
# Z = hierarchy.linkage(X, "average", metric="cosine")
# C = hierarchy.fcluster(Z, threshold, criterion="distance")
# dn = hierarchy.dendrogram(Z, labels=index)
# plt.figure()
# plt.show()
# print(len(set(C)))
# grouped_ids = dict()
# for i, label in enumerate(C):
#     if label not in grouped_ids:
#         grouped_ids[label] = []
#     grouped_ids[label].append(index[i])
# print(grouped_ids)

