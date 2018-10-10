from SPARQLWrapper import SPARQLWrapper, JSON
from config import sparql_queries as sq
from models.co_occurrence import CoOccurrence
from models.publication import Publication
import click
import logging
import click_log

logger = logging.getLogger('root')
click_log.basic_config(logger)


def get_co_authorship(sparql_endpoint, year):
    click.secho("Getting results from {} for year {}".format(sparql_endpoint, year), fg='green')
    query_year = sq.queries['CO-AUTHORSHIP'].format(start=year, end=year + 1)
    logger.debug("Query {}".format(query_year))
    sparql = SPARQLWrapper(sparql_endpoint)
    sparql.setQuery(query_year)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    click.secho("Results: {}".format(len(results["results"]["bindings"])), fg='green')
    co_authorship_edges = []
    for result in results["results"]["bindings"]:
        author_id1 = result["node1"]["value"]
        author_id2 = result["node2"]["value"]
        count = int(result["weight"]["value"])
        date = result["date"]["value"]
        co_authorship_edges.append(CoOccurrence(author_id1, author_id2, count, date))
    return co_authorship_edges


def get_co_authorship_in_range(sparql_endpoint, start_year, end_year, start_month=1, end_month=12):
    click.secho("Getting results from {} for year {}".format(sparql_endpoint, start_year, end_year + 1), fg='green')
    query_year = sq.queries['CO-AUTHORSHIP'].format(start_year=start_year, end_year=end_year, start_month=start_month, end_month=end_month)
    logger.debug("Query {}".format(query_year))
    sparql = SPARQLWrapper(sparql_endpoint)
    sparql.setQuery(query_year)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    click.secho("Results: {}".format(len(results["results"]["bindings"])), fg='green')
    co_authorship_edges = []
    for result in results["results"]["bindings"]:
        author_id1 = result["node1"]["value"]
        author_id2 = result["node2"]["value"]
        count = int(result["weight"]["value"])
        date = result["date"]["value"]
        co_authorship_edges.append(CoOccurrence(author_id1, author_id2, count, date))
    return co_authorship_edges


def get_publications(sparql_endpoint, start_year, end_year, start_month=1, end_month=12):
    click.secho("Getting results from {}-{} for year {}-{}".format(sparql_endpoint, start_year, start_month, end_year, end_month), fg='green')
    query_year = sq.queries['PAPER_ANNOTATIONS'].format(start_year=start_year, start_month=start_month, end_year=end_year, end_month=end_month)
    sparql = SPARQLWrapper(sparql_endpoint)
    sparql.setQuery(query_year)
    sparql.setReturnFormat(JSON)
    click.secho("Executing query", fg='green')
    results = sparql.query().convert()
    click.secho("Results: {}".format(len(results["results"]["bindings"])), fg='green')
    publications = []
    for result in results["results"]["bindings"]:
        date = result["date"]["value"]
        title = result["title"]["value"]
        annotations = result["annotations"]["value"].split('|')
        publications.append(Publication(date=date, title=title, annotations=annotations))
    return publications


def get_publications_with_references(sparql_endpoint, start_year, start_month, end_year, end_month):
    click.secho("Getting results from {}-{} for year {}-{}".format(sparql_endpoint, start_year, start_month, end_year, end_month), fg='green')
    query_year = sq.queries['PAPER_ANNOTATIONS'].format(start_year=start_year, start_month=start_month, end_year=end_year, end_month=end_month)
    logger.debug("Query {}".format(query_year))
    sparql = SPARQLWrapper(sparql_endpoint)
    sparql.setQuery(query_year)
    sparql.setReturnFormat(JSON)
    click.secho("Executing query", fg='green')
    results = sparql.query().convert()
    click.secho("Results: {}".format(len(results["results"]["bindings"])), fg='green')
    publications = []
    for result in results["results"]["bindings"]:
        date = result["date"]["value"]
        title = result["title"]["value"]
        references = result["references"]["value"].split('|')
        publications.append(Publication(date=date, title=title, references=references))
    return publications


def get_publications_by_range(sparql_endpoint, start, end):
    click.secho("Getting results from {} for {} to {}".format(sparql_endpoint, start, end), fg='green')
    query_year = sq.queries['PAPER_ANNOTATIONS'].format(start=start, end=end)
    logger.debug("Query {}".format(query_year))
    sparql = SPARQLWrapper(sparql_endpoint)
    sparql.setQuery(query_year)
    sparql.setReturnFormat(JSON)
    click.secho("Executing query", fg='green')
    results = sparql.query().convert()
    click.secho("Results: {}".format(len(results["results"]["bindings"])), fg='green')
    publications = []
    for result in results["results"]["bindings"]:
        date = result["date"]["value"]
        title = result["title"]["value"]
        annotations = result["annotations"]["value"].split('|')
        publications.append(Publication(date=date, title=title, annotations=annotations))
    return publications
