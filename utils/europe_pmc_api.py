import requests
from config import config, logger
import json
import urllib.parse
from datetime import datetime
import click
from joblib import delayed, Parallel
from tqdm.autonotebook import tqdm


def get_papers_by_keyword(keyword, start_date, end_date, with_references=False):
    click.secho('Harvest for "{}"'.format(keyword), fg="yellow")
    europmc_url = config.get('DEFAULT', 'EUROPE_PMC_SERVICE_URL')
    europmc_query = config.get('DEFAULT', 'EUROPE_PMC_KEYWORDS_QUERY').format(keyword=keyword, start=start_date, end=end_date)
    europmc_rq_url = europmc_url + urllib.parse.quote_plus(europmc_query)
    europmc_results = execute_query_all(europmc_rq_url, True)
    # europmc_results = [{**parse_result(r, with_references)} for r in europmc_results]
    click.secho('Getting references for {} "{}" papers'.format(len(europmc_results), keyword), fg="yellow")
    europmc_results = Parallel(n_jobs=10)(delayed(parse_result)(reference, with_references) for reference in tqdm(europmc_results))
    return europmc_results


def get_citing_papers(pmid, start_date, end_date, with_references=False):
    europmc_url = config.get('DEFAULT', 'EUROPE_PMC_SERVICE_URL')
    europmc_query = config.get('DEFAULT', 'EUROPE_PMC_CITES_QUERY').format(pmid=pmid, start=start_date, end=end_date)
    europmc_rq_url = europmc_url + urllib.parse.quote_plus(europmc_query)
    europmc_results = execute_query_all(europmc_rq_url)
    europmc_results = Parallel(n_jobs=10)(delayed(parse_result)(reference, with_references) for reference in tqdm(europmc_results))
    return europmc_results


def get_paper_by_pmid(pmid, with_references=False):
    europmc_url = config.get('DEFAULT', 'EUROPE_PMC_SERVICE_URL')
    europmc_query = config.get('DEFAULT', 'EUROPE_PMC_PMID_QUERY').format(pmid=pmid)
    europmc_rq_url = europmc_url + urllib.parse.quote_plus(europmc_query)
    results = execute_query(europmc_rq_url)['resultList']['result']
    paper = results[0] if len(results) > 0 else {}
    return parse_result(paper, with_references)


def get_paper_keywords(pmid):
    europmc_url = config.get('DEFAULT', 'EUROPE_PMC_SERVICE_URL')
    europmc_query = config.get('DEFAULT', 'EUROPE_PMC_PMID_QUERY').format(pmid=pmid)
    europmc_rq_url = europmc_url + urllib.parse.quote_plus(europmc_query)
    results = execute_query(europmc_rq_url)['resultList']['result']
    paper = results[0] if len(results) > 0 else {}
    if 'keywordList' in paper:
        keywords = paper['keywordList']['keyword']
    elif 'meshHeadingList' in paper:
        keywords = [meshHeading['descriptorName'] for meshHeading in paper['meshHeadingList']['meshHeading'] if meshHeading['majorTopic_YN'] == 'Y']
    else:
        keywords = []
    return keywords


def get_paper_references(source, paper_id):
    europmc_rq_url = config.get('DEFAULT', 'EUROPE_PMC_PMID_REFERENCES_QUERY').format(source=source, paper_id=paper_id)
    europmc_results = dict()
    try:
        logger.debug("EuroPMC query started: " + europmc_rq_url)
        europmc_results_json = requests.get(europmc_rq_url).text
        europmc_results = json.loads(europmc_results_json)
        logger.debug("EuroPMC query finished")
    except Exception:
        logger.info("EuroPMC query failed: " + europmc_rq_url)
    return europmc_results['referenceList']['reference'] if 'referenceList' in europmc_results else []


def execute_query(query, cursor_mark='%2A'):
    europmc_results = None
    europmc_opts = config.get('DEFAULT', 'EUROPE_PMC_QUERY_OPTS').format(cursor=cursor_mark)
    rq_url = query + europmc_opts
    try:
        logger.debug("EuroPMC query started: " + rq_url)
        europmc_results_json = requests.get(rq_url).text
        europmc_results = json.loads(europmc_results_json)
        logger.debug("EuroPMC query finished")
    except Exception:
        logger.info("EuroPMC query failed: " + rq_url)
    return europmc_results


def execute_query_all(rq_url, verbose=False):
    cursor_mark = '%2A'
    done = False
    results = []
    count = 0
    while not done:
        page_result = execute_query(rq_url, cursor_mark)
        results.extend(page_result['resultList']['result'])
        done = cursor_mark == page_result['nextCursorMark']
        cursor_mark = page_result['nextCursorMark']
        if verbose:
            total = page_result['hitCount']
            click.secho('       Harvested {} of {}'.format(len(results), total), fg="yellow")
    return results


def parse_result(reference, get_references=False):
    author_list = reference.pop('authorList') if 'authorList' in reference else []
    reference['authorList'] = author_list['author'] if not type(author_list) == list else author_list
    grant_list = reference.pop('grantsList') if 'grantsList' in reference else []
    reference['grantsList'] = grant_list['grant'] if 'grant' in grant_list else grant_list
    full_text_url_list = reference.pop('fullTextUrlList') if 'fullTextUrlList' in reference else []
    reference['fullTextUrlList'] = full_text_url_list['fullTextUrl'] if 'fullTextUrl' in full_text_url_list else full_text_url_list
    mesh_heading_list = reference.pop('meshHeadingList') if 'meshHeadingList' in reference else []
    mesh_heading_list = mesh_heading_list['meshHeading'] if 'meshHeading' in mesh_heading_list else mesh_heading_list
    mesh_heading_list = [mesh_term['descriptorName'] for mesh_term in mesh_heading_list]
    reference['meshHeadingList'] = mesh_heading_list
    reference['firstPublicationDate'] = datetime.strptime(reference['firstPublicationDate'], '%Y-%m-%d')
    if get_references:
        reference['references'] = get_paper_references(reference['source'], reference['id'])
    return reference
