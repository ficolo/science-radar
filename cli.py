from commands.network_generation import *
from commands.network_analysis import *
from commands.europe_pmc_harvester import *
from commands.burst_detection import *
from utils.fulltext_downloader import download_fulltext
from utils.bioportal_api import annotate_text
from joblib import delayed, Parallel
import logging
import click_log

logger = logging.getLogger('root')
click_log.basic_config(logger)


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.version_option(version='1.0.0')
def sciradar(debug):
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.ERROR)


@sciradar.command('generate-networks')
@click.option('--biotea-sparql-endpoint',
              default='http://localhost:3030/ds/',
              help='The URL of the Biotea SPARQL Endpoint with the publications metadata and annotations')
@click.option('--dataset-name',
              default='dataset',
              help='The URL of the Biotea SPARQL Endpoint with the publications metadata and annotations')
def generate_networks(biotea_sparql_endpoint, dataset_name):
    """
    Generate Co-citation Network, Co-authorship Network, Co-apparition Network
    from a Biotea SPARQL Endpoint dataset.
    :return:
    """
    click.secho("Generating co-authorship networks", fg='yellow')
    co_authorship_networks = generate_co_authorship_networks_incremental(biotea_sparql_endpoint, dataset_name, 2012, 2018, '../data', True, use_cache=True)
    click.secho("Analysing co-authorship networks", fg='yellow')
    analyse_networks(co_authorship_networks, 'co_authorship_analysis.json')
    click.secho("Generating co-occurrence networks", fg='yellow')
    co_occurrence_networks = get_co_occurrence_network_incremental(biotea_sparql_endpoint, dataset_name, 2012, 2018, '../data', True, use_cache=True)
    click.secho("Analysing co-occurrence networks", fg='yellow')
    analyse_networks(co_occurrence_networks, 'co_occurrence_analysis.json')
    click.secho("Generating co-citation networks", fg='yellow')
    co_citation_networks = get_co_citation_network_incremental(biotea_sparql_endpoint, dataset_name, 2012, 2018, '../data', True, use_cache=True)
    click.secho("Analysing co-citation networks", fg='yellow')
    analyse_networks(co_citation_networks, 'co_citation_analysis.json')
    click.secho("Finished", fg='yellow')


@sciradar.command('harvest')
@click.option('--keywords',
              default='zika',
              help='Set of comma separated keywords to search for')
@click.option('--pmids',
              help='Set of comma separated pmids to search for')
@click.option('--dataset-name',
              default='dataset',
              help='The name of the datatset')
@click.option('--output-path',
              default='.',
              help='The output for the generated files')
@click.option('--start-year',
              default='2010',
              help='The output for the generated files')
@click.option('--end-year',
              default='',
              help='The output for the generated files')
def harvest(keywords, pmids, dataset_name, output_path: str, start_year, end_year):
    end_year = None if end_year == '' else end_year
    keywords = keywords.split(',') if keywords is not None else []
    pmids = pmids.split(',') if pmids is not None else []
    output_path = output_path + '/' if not output_path.endswith('/') else output_path
    output_path += dataset_name + '/'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    click.secho("Harvesting papers", fg='yellow')
    references = harvest_papers_metadata(keywords, pmids, start_year, end_year, include_citing_papers=True)

    click.secho("Getting fulltext", fg='yellow')
    references = Parallel(n_jobs=25)(delayed(get_paper_fulltext)(reference, output_path) for reference in tqdm(references))
    if not os.path.exists(output_path + 'json/'):
        os.makedirs(output_path + 'json/')
    click.secho("Annotating papers", fg='yellow')
    Parallel(n_jobs=25)(delayed(annotate_reference)(reference, output_path) for reference in tqdm(references))


@sciradar.command('burst')
def detect_burst():
    get_word_burst('../data/zika_annotations.csv', ['id', 'date', 'annotations'], 'annotations', dataset_name='Zika')
    # get_word_burst('../data/zika_fulltext.csv', ['id', 'date', 'fullText'], 'fullText', dataset_name='Zika', plain_text=True)
    # get_word_burst('../data/zika_fulltext.csv', ['title', 'date', 'fullText'], 'fullText', dataset_name='Zika', plain_text=True)


def get_paper_fulltext(reference, output_path):
    if os.path.isfile(output_path + 'json/' + reference['id'] + '.json'):
        with open(output_path + 'json/' + reference['id'] + '.json') as f:
            reference = json.load(f)
        return reference
    reference['fullText'] = download_fulltext(reference, output_path)
    return reference


def annotate_reference(reference, output_path):
    if os.path.isfile(output_path + 'json/' + reference['id'] + '.json'):
        with open(output_path + 'json/' + reference['id'] + '.json') as f:
            reference = json.load(f)
        return reference
    if reference['fullText'].strip() is not '':
        reference['annotations'] = annotate_text(reference['fullText'].strip())
    else:
        text = reference['title']
        text += reference['abstractText'] if 'abstractText' in reference else ''
        reference['annotations'] = annotate_text(text)
    with open(output_path + 'json/' + reference['id'] + '.json', 'w') as fp:
        json.dump(reference, fp, default=default, indent=4, sort_keys=True)


def default(o):
    if type(o) is datetime.date or type(o) is datetime.datetime:
        return o.isoformat()


if __name__ == '__main__':
    sciradar()
