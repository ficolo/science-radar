import requests
import json
from config import config, logger


def annotate_text(text):
    r = requests.post(config.get(
        'DEFAULT', 'BIOPORTAL_URL'),
        data={'text': text,
              'apikey': config.get('DEFAULT', 'BIOPORTAL_APIKEY'),
              'ontologies': config.get('DEFAULT', 'ONTOLOGIES'),
              'exclude_numbers': 'true',
              'exclude_synonyms': 'false',
              'expand_class_hierarchy': 'true',
              'class_hierarchy_max_level': '2',
              'include': 'prefLabel',
              'display_context': 'false',
              'format': 'json'
              })
    annotations = []
    try:
        for annotation in r.json():
            annotation_dict = dict()
            annotation_dict['id'] = annotation['annotatedClass']['@id']
            annotation_dict['ontology'] = annotation['annotatedClass']['links']['ontology']
            annotation_dict['bioportalLink'] = annotation['annotatedClass']['links']['self']
            if 'prefLabel' not in annotation['annotatedClass']:
                continue
            annotation_dict['prefLabel'] = annotation['annotatedClass']['prefLabel']
            annotations.append(annotation_dict)
        return annotations
    except json.decoder.JSONDecodeError:
        return []
    except TypeError:
        logger.debug('Bad response from the Bioportal Annotator')
        return []


def get_pref_label(bioportal_link):
    r = requests.get(
        bioportal_link + '?display_links=false&display_context=false&apikey=' + config.get('DEFAULT',
                                                                                           'BIOPORTAL_APIKEY'))
    term = r.json()
    return term['prefLabel']
