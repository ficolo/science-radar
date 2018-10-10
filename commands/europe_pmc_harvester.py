from utils.europe_pmc_api import *
from tqdm.autonotebook import tqdm

import datetime


def harvest_papers_metadata(keywords, pmids, start=2010, end=None, include_citing_papers=False):
    if end is None:
        end = datetime.datetime.now().year
    reference_index = []
    references = []
    for pmid in pmids:
        if 'MED_' + pmid not in reference_index:
            reference = get_paper_by_pmid(pmid, True)
            references.append(reference)
            ref_id = reference['source'] + '_' + reference['id']
            reference_index.append(ref_id)
        for reference in get_citing_papers(pmid, start, end):
            ref_id = reference['source'] + '_' + reference['id']
            if ref_id not in reference_index:
                references.append(reference)
                reference_index.append(ref_id)

    for keyword in keywords:
        for reference in get_papers_by_keyword(keyword, start, end, True):
            ref_id = reference['source'] + '_' + reference['id']
            if ref_id not in reference_index:
                references.append(reference)
                reference_index.append(ref_id)
    if include_citing_papers:
        citing_papers = []
        click.secho('Harvesting citations for {} papers'.format(len(references)), fg="yellow")
        for reference in tqdm(references):
            if reference['citedByCount'] == 0:
                continue
            citing_papers.extend(get_citing_papers(reference['id'], start, end, True))
        for citing_paper in citing_papers:
            ref_id = citing_paper['source'] + '_' + citing_paper['id']
            if ref_id not in reference_index:
                references.append(citing_paper)
                reference_index.append(ref_id)
    return references

