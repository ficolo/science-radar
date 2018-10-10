from graph_tool.all import *
import datetime
from utils import csv_parser as csv, sparql_access as sparql
from models.co_occurrence import CoOccurrence
import os.path
import click
from tqdm.autonotebook import tqdm
from utils import mongodb_access
from joblib import Parallel, delayed
from time import time
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.cluster import hierarchy
from sklearn.cluster import DBSCAN


def generate_co_authorship_network_by_year(year, output_file='output.gt', save=False, sparql_endpoint=None,
                                           mongo_config=None):
    """
    Generates a co-authorship Network for the given Biotea SPARQL dataset and, if desired, saved to a GraphML file
    :return: Graph
    """
    co_authorship_edges = []
    if sparql_endpoint is None and mongo_config is None:
        return Graph()
    if sparql_endpoint:
        co_authorship_edges = sparql.get_co_authorship(sparql_endpoint, year)
    elif mongo_config:
        publications = mongodb_access.get_co_authorship(mongo_config['database'], mongo_config['collection'],
                                                        mongo_config['host'], mongo_config['port'], year, 1, year + 1,
                                                        12)
        co_authorship_edges = get_co_occurrences(publications, 'authors')
    co_authorship_network = generate_network_from_edges(co_authorship_edges)
    if save:
        co_authorship_network.save(output_file)
    return co_authorship_network


def generate_co_authorship_networks_incremental(sparql_endpoint, dataset_name, start_year, end_year, output_path='.',
                                                save=False, use_cache=False, mongo_config=None):
    networks = {}
    co_authorship_network = None
    for year, month in month_year_iter(1, start_year, 1, end_year):
        click.secho("   Generating network for range {}-{} to {}-{}".format(start_year, 1, year, month), fg='yellow')
        network_range = '{start_year}-{start_month} to {current_year}-{current_month}'.format(start_year=start_year,
                                                                                              start_month=1,
                                                                                              current_year=year,
                                                                                              current_month=month)
        output_file = "{output_path}/{dataset}_{range}_authorship.gt".format(output_path=output_path,
                                                                             dataset=dataset_name,
                                                                             range=network_range)
        if use_cache and os.path.isfile(output_file):
            networks[network_range] = load_graph(output_file)
            co_authorship_network = networks[network_range]
            continue
        if mongo_config is None:
            co_authorship_edges = sparql.get_co_authorship_in_range(sparql_endpoint, start_year, year, 1, month)
        else:
            publications = mongodb_access.get_co_authorship(mongo_config['database'], mongo_config['collection'],
                                                            mongo_config['host'], mongo_config['port'],
                                                            start_year, 1, year, month)
            co_authorship_edges = get_co_occurrences(publications, 'authors')
        co_authorship_network = generate_network_from_edges(co_authorship_edges, co_authorship_network,
                                                            include_date=False)
        networks[network_range] = co_authorship_network
        if save:
            co_authorship_network.save(output_file)
    return networks


def get_co_occurrence_network_by_year(year, output_file='output.gt', save=False, sparql_endpoint=None, csv_file=None):
    if sparql_endpoint is None and csv_file is None:
        return Graph()
    if sparql_endpoint:
        publications = sparql.get_publications(sparql_endpoint, year)
    if csv_file:
        publications = csv.get_co_authorship(year)
    co_occurrences = get_co_occurrences(publications, 'annotations')
    co_occurrence_network = generate_network_from_edges(co_occurrences)
    if save:
        co_occurrence_network.save(output_file)
    return co_occurrence_network


def get_co_occurrence_network_incremental(sparql_endpoint, dataset_name, start_year, end_year, output_path='.',
                                          save=False, use_cache=False, mongo_config=None):
    networks = {}
    co_occurrence_network = None
    previous_month = 1
    previous_year = start_year
    publications_acc = []
    for year, month in month_year_iter(1, start_year, 1, end_year):
        click.secho("   Generating network for range {}-{} to {}-{}".format(start_year, 1, year, month), fg='yellow')
        network_range = '{start_year}-{start_month} to {current_year}-{current_month}'.format(start_year=start_year,
                                                                                              start_month=1,
                                                                                              current_year=year,
                                                                                              current_month=month)
        output_file = "{output_path}/{dataset}_{range}_co_occurrence.gt".format(output_path=output_path,
                                                                                dataset=dataset_name,
                                                                                range=network_range)
        if use_cache and os.path.isfile(output_file):
            networks[network_range] = load_graph(output_file)
            co_occurrence_network = networks[network_range]
            continue
        if mongo_config is None:
            publications = sparql.get_publications(sparql_endpoint, previous_year, year, previous_month, month)
        else:
            publications = mongodb_access.get_co_occurrence(mongo_config['database'], mongo_config['collection'],
                                                            mongo_config['host'], mongo_config['port'],
                                                            previous_year, previous_month, year, month)
        publications_acc.extend(publications)
        co_occurrence_edges = get_co_occurrences(publications_acc, 'annotations')
        co_occurrence_network = generate_network_from_edges(co_occurrence_edges, co_occurrence_network)
        networks[network_range] = co_occurrence_network
        if save:
            co_occurrence_network.save(output_file)
        previous_year = year
        previous_month = month
    return networks


def get_co_citation_network_by_year(year, output_file='output.gt', save=False, sparql_endpoint=None, csv_file=None):
    if sparql_endpoint is None and csv_file is None:
        return Graph()
    if sparql_endpoint:
        publications = sparql.get_publications_with_references(sparql_endpoint, year)
    if csv_file:
        publications = csv.get_co_authorship(year)
    co_occurrences = get_co_occurrences(publications, 'references')
    co_occurrence_network = generate_network_from_edges(co_occurrences)
    if save:
        co_occurrence_network.save(output_file)
    return co_occurrence_network


def get_co_citation_network_incremental(sparql_endpoint, dataset_name, start_year, end_year, output_path='.',
                                        save=False, use_cache=False, mongo_config=None):
    networks = {}
    co_occurrence_network = None
    for year, month in month_year_iter(1, start_year, 1, end_year):
        descriptors = None
        click.secho("   Generating network for range {}-{} to {}-{}".format(start_year, 1, year, month), fg='yellow')
        network_range = '{start_year}-{start_month} to {current_year}-{current_month}'.format(start_year=start_year,
                                                                                              start_month=1,
                                                                                              current_year=year,
                                                                                              current_month=month)
        output_file = "{output_path}/{dataset}_{range}_co_citation.gt".format(output_path=output_path,
                                                                              dataset=dataset_name,
                                                                              range=network_range)
        if use_cache and os.path.isfile(output_file):
            networks[network_range] = load_graph(output_file)
            co_occurrence_network = networks[network_range]
            continue
        if mongo_config is None:
            publications = sparql.get_publications_with_references(sparql_endpoint, start_year, 1, year, month)
        else:
            publications, descriptors = mongodb_access.get_co_citation(mongo_config['database'], mongo_config['collection'],
                                                                       mongo_config['host'], mongo_config['port'],
                                                                       start_year, 1, year, month)
        co_occurrence_edges = get_co_occurrences(publications, 'references')
        co_occurrence_network = generate_network_from_edges(co_occurrence_edges, co_occurrence_network)
        if descriptors is not None:
            annotations_prop = co_occurrence_network.new_vertex_property('vector<string>')
            co_occurrence_network.vertex_properties['annotations'] = annotations_prop
            keywords_prop = co_occurrence_network.new_vertex_property('vector<string>')
            co_occurrence_network.vertex_properties['keywords'] = keywords_prop
            cited_by_count_prop = co_occurrence_network.new_vertex_property('int')
            co_occurrence_network.vertex_properties['citedByCount'] = cited_by_count_prop
            for v in co_occurrence_network.vertices():
                v_id = co_occurrence_network.vertex_properties['label'][v]
                co_occurrence_network.vertex_properties['annotations'][v] = descriptors[v_id]['annotations'] if v_id in descriptors else []
                co_occurrence_network.vertex_properties['keywords'][v] = descriptors[v_id]['keywords'] if v_id in descriptors else []
                co_occurrence_network.vertex_properties['citedByCount'][v] = descriptors[v_id]['citedByCount'] if v_id in descriptors else 0
        networks[network_range] = co_occurrence_network
        if save:
            co_occurrence_network.save(output_file)
    return networks


def get_co_occurrences(publications, field):
    publications_by_annotation = {}
    for index, publication in enumerate(publications):
        for annotation in getattr(publication, field):
            if annotation not in publications_by_annotation:
                publications_by_annotation[annotation] = set()
            publications_by_annotation[annotation].add(index)
    annotations = sorted(publications_by_annotation)
    co_occurrences = Parallel(n_jobs=1)(delayed(get_co_occurrences_aux)(index, annotation1, annotations, publications_by_annotation) for index, annotation1 in enumerate(annotations))
    co_occurrences = [item for sublist in co_occurrences for item in sublist]
    return co_occurrences


def get_co_occurrences_aux(index, value1, sorted_keys, value_index):
    co_occurrences = []
    for value2 in sorted_keys[index + 1:]:
        weight = len(value_index[value1].intersection(value_index[value2]))
        if weight > 0:
            co_occurrences.append(CoOccurrence(value1, value2, weight))
    return co_occurrences


def get_co_occurrence(annotation1, annotation2, publications_by_annotation):
    weight = len(publications_by_annotation[annotation1].intersection(publications_by_annotation[annotation2]))
    if weight > 0:
        return CoOccurrence(annotation1, annotation2, weight)
    else:
        return False


def generate_network_from_edges(network_edges, existing_network=None, include_date=False):
    if existing_network is None:
        existing_network = Graph(directed=False)

        label_prop = existing_network.new_vertex_property("string")
        existing_network.vertex_properties['label'] = label_prop

        if include_date:
            full_date_prop = existing_network.new_vertex_property("string")
            existing_network.vertex_properties['fulldate'] = full_date_prop
            year_prop = existing_network.new_vertex_property("int")
            existing_network.vertex_properties['year'] = year_prop
            days_prop = existing_network.new_vertex_property("int")
            existing_network.vertex_properties['days'] = days_prop

        weight_prop = existing_network.new_edge_property("int")
        existing_network.edge_properties['weight'] = weight_prop

    vertex_index = {x: i for i, x in enumerate(existing_network.vertex_properties['label'])}
    for edge in tqdm(network_edges):
        # a = find_vertex(existing_network, existing_network.vertex_properties['label'], edge.a)
        # a = a[0] if len(a) > 0 else None
        # b = find_vertex(existing_network, existing_network.vertex_properties['label'], edge.b)
        # b = b[0] if len(b) > 0 else None
        a = vertex_index[edge.a] if edge.a in vertex_index else None
        b = vertex_index[edge.b] if edge.b in vertex_index else None
        if include_date:
            full_date = datetime.datetime.strptime(edge.date, "%Y-%m-%dT%H:%M:%S")
            days = (full_date - datetime.datetime(1970, 1, 1)).days
        if a is None:
            a = existing_network.add_vertex()
            existing_network.vertex_properties['label'][a] = edge.a
            vertex_index[edge.a] = a
            if include_date:
                existing_network.vertex_properties['year'][a] = full_date.year
                existing_network.vertex_properties['fulldate'][a] = edge.date
                existing_network.vertex_properties['days'][a] = days
        if b is None:
            b = existing_network.add_vertex()
            existing_network.vertex_properties['label'][b] = edge.b
            vertex_index[edge.b] = b
            if include_date:
                existing_network.vertex_properties['year'][b] = full_date.year
                existing_network.vertex_properties['fulldate'][b] = edge.date
                existing_network.vertex_properties['days'][b] = days
        graph_edge = existing_network.edge(a, b)
        if graph_edge is None:
            graph_edge = existing_network.add_edge(a, b)
            existing_network.edge_properties['weight'][graph_edge] = 0
        existing_network.edge_properties['weight'][graph_edge] += edge.weight
    return existing_network


def month_year_iter(start_month, start_year, end_month, end_year):
    ym_start = 12 * start_year + start_month - 1
    ym_end = 12 * end_year + end_month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m + 1


# mongo_config = {
#     'database': 'publications',
#     'collection': 'zika',
#     'host': 'localhost',
#     'port': 27017
# }
#
# output_path = '/Users/federico/git/science-radar/data/sciradar/zika/'
#
# co_citation_networks = get_co_citation_network_incremental('', 'zika', 2010, 2018, output_path=output_path + 'gt',
#                                                            mongo_config=mongo_config, save=True, use_cache=True)
#
#
# references, index = mongodb_access.get_references_annotations('publications', 'zika', 'localhost', 27017, 2010, 1, 2018, 1)
# t0 = time()
# print('vectorizing')
# vectorizer = TfidfVectorizer(use_idf=True)
# X = vectorizer.fit_transform(references)
# print("n_samples: %d, n_features: %d" % X.shape)
# db = DBSCAN(metric='cosine', eps=0.5).fit(X)
# labels = db.labels_
#
# # Number of clusters in labels, ignoring noise if present.
# n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
# unique_labels = set(labels)
# print(len(unique_labels))
# pmid_cluster_map = dict()
# for i, label in enumerate(labels):
#     pmid_cluster_map[index[i]] = label
# g_grouped = co_citation_networks['2010-1 to 2017-12']
#
# group_prop = g_grouped.new_vertex_property("int")
# g_grouped.vertex_properties['group'] = group_prop
#
# for v in g_grouped.vertices():
#     pmid = g_grouped.vertex_properties['label'][v]
#     g_grouped.vertex_properties['group'][v] = pmid_cluster_map[pmid] if pmid in pmid_cluster_map else -1
# g_grouped = GraphView(g_grouped, vfilt=lambda v: g_grouped.vertex_properties['group'][v] > -1 and  g_grouped.vertex_properties['group'][v] is not None).copy()
# g_grouped.purge_vertices()
# g_grouped.save(output_path + 'gt/clustered_2010_2017.xml.gz')