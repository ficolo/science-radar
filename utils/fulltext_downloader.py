from urllib import request
import tarfile
import requests
import time
import json
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO, BytesIO
from bs4 import BeautifulSoup
import os.path
from config import config, logger
from bs4.element import Comment


def download_fulltext(reference, output_path, save=False):
    if not os.path.exists(output_path + 'txt/'):
        os.makedirs(output_path + 'txt/')
    if not os.path.exists(output_path + 'xml/'):
        os.makedirs(output_path + 'xml/')
    url_list = reference['fullTextUrlList']
    urls_by_type = {url['documentStyle']: url['url'] for url in url_list}
    nxml_file_name = output_path + 'xml/' + reference['pmcid'] + '.nxml' if 'pmcid' in reference else None
    txt_file_name = output_path + 'txt/' + reference['id'] + '.txt'
    text = ''

    if nxml_file_name is not None:
        if os.path.isfile(nxml_file_name) or get_xml(reference, output_path + 'xml/'):
            with open(nxml_file_name, 'r') as xml_file:
                text = process_xml(xml_file.read())
    elif os.path.isfile(txt_file_name):
        with open(txt_file_name, 'r') as txt_file:
            text = txt_file.read()
    elif 'html' in urls_by_type:
        text = process_html(urls_by_type['html'])
    elif 'pdf' in urls_by_type:
        text = process_pdf(urls_by_type['pdf'])
    elif 'doi' in urls_by_type:
        text = process_doi(urls_by_type['doi'])
    else:
        text = ''
    if save and not os.path.isfile(output_path + txt_file_name) and len(text) > 0:
        with open(output_path + txt_file_name, 'w') as txt_file:
            txt_file.write(text)
    return text


def process_html(url):
    response = process_url(url)
    if not response:
        return ''
    body = response.text.replace('\n', ' ').replace('<sup>', '&lt;').replace('</sup>', '&gt;')
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t.strip() for t in visible_texts)


def process_xml(xml_text):
    if not xml_text:
        return ''
    xml_text = xml_text.replace('\n', ' ').replace('<sup>', '&lt;').replace('</sup>', '&gt;').replace('<italic>', '').replace('</italic>', '')
    soup = BeautifulSoup(xml_text, 'xml')
    xml_content = soup.findAll(text=True)
    visible_texts = filter(tag_visible, xml_content)
    return u" ".join(t.strip() for t in visible_texts)


def process_pdf(url):
    response = process_url(url)
    if not response:
        return ''
    pdf_content = response.content
    pdf_content = BytesIO(pdf_content)
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos=set()

    for page in PDFPage.get_pages(pdf_content,
                                  pagenos,
                                  maxpages=maxpages,
                                  password=password,
                                  caching=caching,
                                  check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()
    device.close()
    retstr.close()
    return text


def process_doi(url):
    url = resolve_doi(url)
    return process_html(url)


def process_url(url, times=0):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36 Edge/12.0'
    }
    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        time.sleep(5)
        logger.debug('Retrying {}'.format(url))
        if times < 2:
            return process_url(url, times + 1)
        else:
            return None
    return response


def resolve_doi(doi_url):
    doi = doi_url.replace('https://doi.org/', '')
    doi_resolver_request = config.get('DEFAULT', 'DOI_RESOLVER_URL').format(doi=doi)
    response = requests.get(doi_resolver_request)
    response = json.loads(response.content)
    if 'values' in response and response['values']:
        return response['values'][0]['data']['value']
    else:
        return doi_url


def get_xml(reference, output_path):
    if 'pmcid' not in reference:
        return False
    rq_url = config.get('DEFAULT', 'PMC_AOI_URL').format(pmcid=reference['pmcid'])
    try:
        logger.debug("PMC OA query started: " + rq_url)
        pmc_xml_record = requests.get(rq_url).text
        pmc_xml_soup = BeautifulSoup(pmc_xml_record, 'xml')
        if pmc_xml_soup.find('error'):
            logger.debug("File not found in PMC-OA: " + rq_url)
            return False
        link_element = pmc_xml_soup.find('link')
        href_value = link_element['href']
        if href_value:
            extract_tgz(href_value, output_path + '/', reference['pmcid'])
            return reference['pmcid']
    except Exception as e:
        logger.debug("PMC OA query failed " + rq_url + ': ' + str(e))
        return False


def extract_tgz(ftp_url, out_path, pmcid):
    tmpfile = BytesIO()
    ftpstream = request.urlopen(ftp_url)
    while True:
        s = ftpstream.read(16384)
        if not s:
            break
        tmpfile.write(s)
    ftpstream.close()
    tmpfile.seek(0)
    tar = tarfile.open(fileobj=tmpfile, mode="r:gz")
    for member in tar.getmembers():
        if member.isreg() and member.name.endswith('.nxml'):
            member.name = pmcid + '.nxml'
            tar.extract(member, out_path + '/')
    tar.close()
    tmpfile.close()


def tag_visible(element):
    if isinstance(element, Comment):
        return False
    if element.parent.name in ['article-title', 'p', 'title']:
        return True
    return False
