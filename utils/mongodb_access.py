from pymongo import MongoClient
import json
import os
from datetime import datetime
from models.publication import Publication
import re


def save_json(file_path, database, collection, mongo_host):
    client = MongoClient(mongo_host, 27017)
    db = client[database]
    collection_currency = db[collection]

    with open(file_path) as f:
        file_data = json.load(f)

    collection_currency.insert(file_data)
    client.close()


def save_directory(dir_path, database, collection, mongo_host):
    for subdir, dirs, files in os.walk(dir_path):
        for file in files:
            file_path = subdir + os.sep + file

            if file_path.endswith(".json"):
                save_json(file_path, database, collection, mongo_host)


def get_all(mongo_host, mongo_port, database, collection):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    return collection.find({})


def update_document(mongo_host, mongo_port, database, collection, document):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection_currency = db[collection]
    mongo_id = document['_id']
    collection_currency.update_one({'_id': mongo_id}, {"$set": document}, upsert=False)
    client.close()


def get_co_authorship(database, collection, mongo_host, mongo_port, start_year, start_month, end_year, end_month):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    start_date = datetime(start_year, start_month, 1, 0, 0, 0)
    end_date = datetime(end_year, end_month, 1, 0, 0, 0)
    pipeline = [
        {
            "$addFields": {
                "publicationDate": {
                    "$dateFromString": {
                        "dateString": "$firstPublicationDate",
                        "format": "%Y-%m-%dT%H:%M:%S"
                    }
                }
            }
        },
        {
            "$match": {
                "publicationDate": {"$gt": start_date, "$lt": end_date}
            }
        }
        ,
        {
            "$project": {
                "id": 1.0,
                "authorList.firstName": 1.0,
                "authorList.lastName": 1.0,
                "firstPublicationDate": 1.0
            }
        },
        {
            "$unwind": {
                "path": "$authorList"
            }
        },
        {
            "$project": {
                "id": 1.0,
                "firstPublicationDate": 1.0,
                "authorList.name": {
                    "$concat": [
                        {
                            "$toUpper": "$authorList.firstName"
                        },
                        " ",
                        {
                            "$toUpper": "$authorList.lastName"
                        }
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "id": "$id",
                    "date": "$firstPublicationDate"
                },
                "authors": {
                    "$addToSet": "$authorList.name"
                }
            }
        }
    ]
    publications = []
    for paper in collection.aggregate(pipeline, allowDiskUse=True):
        publication = Publication(publication_id=paper['_id']['id'], title=paper['_id']['id'],
                                  date=paper['_id']['date'],
                                  authors=[author.replace(' ', '_').replace('-', '_') for author in paper['authors']])
        publications.append(publication)
    return publications


def get_co_occurrence(database, collection, mongo_host, mongo_port, start_year, start_month, end_year, end_month):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    start_date = datetime(start_year, start_month, 1, 0, 0, 0)
    end_date = datetime(end_year, end_month, 1, 0, 0, 0)
    pipeline = [
        {
            "$addFields": {
                "publicationDate": {
                    "$dateFromString": {
                        "dateString": "$firstPublicationDate",
                        "format": "%Y-%m-%dT%H:%M:%S"
                    }
                }
            }
        },
        {
            "$match": {
                "publicationDate": {"$gt": start_date, "$lt": end_date}
            }
        }
        ,
        {
            "$project": {
                "id": 1.0,
                "annotations.prefLabel": 1.0,
                "annotations.ontology": 1.0,
                "firstPublicationDate": 1.0
            }
        },
        {
            "$unwind": {
                "path": "$annotations"
            }
        },
        {
            "$match": {
                "annotations.ontology": "http://data.bioontology.org/ontologies/NCIT"
            }
        },
        {
            "$project": {
                "id": 1.0,
                "firstPublicationDate": 1.0,
                "annotations.prefLabel": {
                    "$toUpper": "$annotations.prefLabel"
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "id": "$id",
                    "date": "$firstPublicationDate"
                },
                "annotations": {
                    "$addToSet": "$annotations.prefLabel"
                }
            }
        }
    ]
    publications = []
    for paper in collection.aggregate(pipeline, allowDiskUse=True):
        publication = Publication(publication_id=paper['_id']['id'], title=paper['_id']['id'],
                                  date=paper['_id']['date'],
                                  annotations=[annotation.encode('utf-8').strip() for annotation in
                                               paper['annotations']])
        publications.append(publication)
    return publications


def get_co_citation(database, collection, mongo_host, mongo_port, start_year, start_month, end_year, end_month):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    start_date = datetime(start_year, start_month, 1, 0, 0, 0)
    end_date = datetime(end_year, end_month, 1, 0, 0, 0)
    pipeline = [
        {
            "$addFields": {
                "publicationDate": {
                    "$dateFromString": {
                        "dateString": "$firstPublicationDate",
                        "format": "%Y-%m-%dT%H:%M:%S"
                    }
                }
            }
        },
        {
            "$match": {
                "publicationDate": {"$gt": start_date, "$lt": end_date}
            }
        }
        ,
        {
            "$project": {
                "id": 1.0,
                "references.id": 1.0,
                "references.annotations": 1.0,
                "references.keywords": 1.0,
                "firstPublicationDate": 1.0
            }
        },
        {
            "$unwind": {
                "path": "$references"
            }
        },
        {
            "$match": {
                "references.id": {
                    "$nin": [
                        None,
                        ""
                    ]
                }
            }
        },
        {
            "$project": {
                "id": 1.0,
                "firstPublicationDate": 1.0,
                "references.id": {
                    "$toUpper": "$references.id"
                },
                "references.annotations": 1.0,
                "references.keywords": 1.0,
            }
        },
        {
            "$group": {
                "_id": {
                    "id": "$id",
                    "date": "$firstPublicationDate"
                },
                "references": {
                    "$addToSet": "$references"
                }
            }
        }
    ]
    publications = []
    references_descriptors = dict()
    for paper in collection.aggregate(pipeline, allowDiskUse=True):
        publication = Publication(publication_id=paper['_id']['id'], title=paper['_id']['id'],
                                  date=paper['_id']['date'],
                                  references=[reference['id'] for reference in paper['references']])
        publications.append(publication)
        for reference in paper['references']:
            if reference['id'] not in references_descriptors:
                references_descriptors[reference['id']] = dict(annotations=[], keywords=[], citedByCount=0)
            reference_annotations = []
            if 'annotations' in reference:
                for annotation in reference['annotations']:
                    reference_annotations.append(annotation['prefLabel'].upper())
            references_descriptors[reference['id']]['annotations'].extend(reference_annotations)
            references_descriptors[reference['id']]['keywords'].extend(
                reference['keywords'] if 'keywords' in reference else [])
            references_descriptors[reference['id']]['citedByCount'] += 1
    for reference in references_descriptors.keys():
        references_descriptors[reference]['annotations'] = list(set(references_descriptors[reference]['annotations']))
        references_descriptors[reference]['keywords'] = list(
            set([keyword.upper() for keyword in references_descriptors[reference]['keywords']]))
    return publications, references_descriptors


def get_references_annotations(database, collection, mongo_host, mongo_port, start_year, start_month, end_year,
                               end_month):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    start_date = datetime(start_year, start_month, 1, 0, 0, 0)
    end_date = datetime(end_year, end_month, 1, 0, 0, 0)
    pipeline = [
        {
            "$addFields": {
                "publicationDate": {
                    "$dateFromString": {
                        "dateString": "$firstPublicationDate",
                        "format": "%Y-%m-%dT%H:%M:%S"
                    }
                }
            }
        },
        {
            "$match": {
                "publicationDate": {
                    "$gt": start_date,
                    "$lt": end_date
                }
            }
        },
        {
            "$project": {
                "references.id": 1.0,
                "references.annotations": 1.0
            }
        },
        {
            "$unwind": {
                "path": "$references"
            }
        },
        {
            "$match": {
                "references.id": {
                    "$nin": [
                        None,
                        ""
                    ]
                }
            }
        },
        {
            "$project": {
                "references.id": {
                    "$toUpper": "$references.id"
                },
                "references.annotations": 1.0
            }
        },
        {
            "$unwind": {
                "path": "$references.annotations"
            }
        },
        {
            "$project": {
                "references.id": 1.0,
                "references.annotations.prefLabel": {
                    "$toUpper": "$references.annotations.prefLabel"
                }
            }
        },
        {
            "$match": {
                "references.annotations.prefLabel": {'$not': re.compile("\d.+", re.IGNORECASE)}
            }
        },
        {
            "$group": {
                "_id": "$references.id",
                "annotations": {
                    "$push": "$references.annotations.prefLabel"
                }
            }
        }
    ]
    references = []
    index = []
    for reference in collection.aggregate(pipeline, allowDiskUse=True):
        references.append(', '.join(reference['annotations']))
        index.append(reference['_id'])
    return references, index


def get_references_annotations(database, collection, mongo_host, mongo_port, start_year, start_month, end_year,
                               end_month):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    start_date = datetime(start_year, start_month, 1, 0, 0, 0)
    end_date = datetime(end_year, end_month, 1, 0, 0, 0)
    pipeline = [
        {
            "$addFields": {
                "publicationDate": {
                    "$dateFromString": {
                        "dateString": "$firstPublicationDate",
                        "format": "%Y-%m-%dT%H:%M:%S"
                    }
                }
            }
        },
        {
            "$match": {
                "publicationDate": {
                    "$gt": start_date,
                    "$lt": end_date
                }
            }
        },
        {
            "$project": {
                "references.id": 1.0,
                "references.annotations": 1.0
            }
        },
        {
            "$unwind": {
                "path": "$references"
            }
        },
        {
            "$match": {
                "references.id": {
                    "$nin": [
                        None,
                        ""
                    ]
                }
            }
        },
        {
            "$project": {
                "references.id": {
                    "$toUpper": "$references.id"
                },
                "references.annotations": 1.0
            }
        },
        {
            "$unwind": {
                "path": "$references.annotations"
            }
        },
        {
            "$project": {
                "references.id": 1.0,
                "references.annotations.prefLabel": {
                    "$toUpper": "$references.annotations.prefLabel"
                }
            }
        },
        {
            "$match": {
                "references.annotations.prefLabel": {'$not': re.compile("\d.+", re.IGNORECASE)}
            }
        },
        {
            "$group": {
                "_id": "$references.id",
                "annotations": {
                    "$addToSet": "$references.annotations.prefLabel"
                }
            }
        }
    ]
    references = []
    index = []
    for reference in collection.aggregate(pipeline, allowDiskUse=True):
        references.append(', '.join(reference['annotations']))
        index.append(reference['_id'])
    return references, index


def get_references_count(database, collection, mongo_host, mongo_port, start_year, start_month, end_year,
                         end_month):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    start_date = datetime(start_year, start_month, 1, 0, 0, 0)
    end_date = datetime(end_year, end_month, 1, 0, 0, 0)
    pipeline = [
        {
            "$addFields": {
                "publicationDate": {
                    "$dateFromString": {
                        "dateString": "$firstPublicationDate",
                        "format": "%Y-%m-%dT%H:%M:%S"
                    }
                }
            }
        },
        {
            "$match": {
                "publicationDate": {
                    "$gt": start_date,
                    "$lt": end_date
                }
            }
        },
        {
            "$project": {
                "references.id": 1.0,
                "references.annotations": 1.0
            }
        },
        {
            "$unwind": {
                "path": "$references"
            }
        },
        {
            "$match": {
                "references.id": {
                    "$nin": [
                        None,
                        ""
                    ]
                }
            }
        },
        {
            "$project": {
                "references.id": {
                    "$toUpper": "$references.id"
                }
            }
        },
        {
            "$group": {
                "_id": "$references.id",
                "citedByCount": {
                    "$sum": 1.0
                }
            }
        },
        {
            "$sort": {
                "citedByCount": -1
            }
        },
        # {
        #     '$limit': 500
        # }
    ]
    citation_count = []
    for reference in collection.aggregate(pipeline, allowDiskUse=True):
        citation_count.append(reference['_id'])
    return citation_count


def get_paper_by_month(database, collection, mongo_host, mongo_port):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    pipeline = [
        {
            '$group': {
                '_id': {'$substr': ['$firstPublicationDate', 0, 7]},
                'publicationCount': {'$sum': 1}
            }
        }
    ]
    papers_by_month = dict()
    for month_count in collection.aggregate(pipeline, allowDiskUse=True):
        papers_by_month[month_count['_id']] = month_count['publicationCount']
    return papers_by_month


def get_unique_authors_by_month(database, collection, mongo_host, mongo_port):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    pipeline = [
        {
            "$project": {
                "firstPublicationDate": 1.0,
                "authorList.firstName": 1.0,
                "authorList.lastName": 1.0
            }
        },
        {
            "$unwind": {
                "path": "$authorList"
            }
        },
        {
            "$project": {
                "firstPublicationDate": 1.0,
                "authorList.name": {
                    "$concat": [
                        {
                            "$toUpper": "$authorList.firstName"
                        },
                        " ",
                        {
                            "$toUpper": "$authorList.lastName"
                        }
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$substr": [
                        "$firstPublicationDate",
                        0.0,
                        7.0
                    ]
                },
                "authors": {
                    "$addToSet": "$authorList.name"
                }
            }
        },
        {
            "$unwind": {
                "path": "$authors"
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "authorsCount": {
                    "$sum": 1.0
                }
            }
        }
    ]
    authors_by_month = dict()
    for month_count in collection.aggregate(pipeline, allowDiskUse=True):
        authors_by_month[month_count['_id']] = month_count['authorsCount']
    return authors_by_month


def get_unique_references_by_month(database, collection, mongo_host, mongo_port):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    pipeline = [
        {
            "$project": {
                "firstPublicationDate": 1.0,
                "references.id": 1.0
            }
        },
        {
            "$unwind": {
                "path": "$references"
            }
        },
        {
            "$match": {
                "references.id": {
                    "$exists": True
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$substr": [
                        "$firstPublicationDate",
                        0.0,
                        7.0
                    ]
                },
                "referenceIds": {
                    "$addToSet": "$references.id"
                }
            }
        },
        {
            "$unwind": {
                "path": "$referenceIds"
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "referenceCount": {
                    "$sum": 1.0
                }
            }
        }
    ]
    references_by_month = dict()
    for month_count in collection.aggregate(pipeline, allowDiskUse=True):
        references_by_month[month_count['_id']] = month_count['referenceCount']
    return references_by_month


def get_unique_keywords_by_month(database, collection, mongo_host, mongo_port):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    pipeline = [
        {
            "$project": {
                "firstPublicationDate": 1.0,
                "keywordList.keyword": 1.0
            }
        },
        {
            "$unwind": {
                "path": "$keywordList.keyword"
            }
        },
        {
            "$group": {
                "_id": {
                    "$substr": [
                        "$firstPublicationDate",
                        0.0,
                        7.0
                    ]
                },
                "keywords": {
                    "$addToSet": "$keywordList.keyword"
                }
            }
        },
        {
            "$unwind": {
                "path": "$keywords"
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "keywordCount": {
                    "$sum": 1.0
                }
            }
        }
    ]
    keywords_by_month = dict()
    for month_count in collection.aggregate(pipeline, allowDiskUse=True):
        keywords_by_month[month_count['_id']] = month_count['keywordCount']
    return keywords_by_month


def get_paper_count(database, collection, mongo_host, mongo_port, start_year, start_month, end_year, end_month):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    start_date = datetime(start_year, start_month, 1, 0, 0, 0)
    end_date = datetime(end_year, end_month, 1, 0, 0, 0)
    pipeline = [
        {
            "$addFields": {
                "publicationDate": {
                    "$dateFromString": {
                        "dateString": "$firstPublicationDate",
                        "format": "%Y-%m-%dT%H:%M:%S"
                    }
                }
            }
        },
        {
            "$match": {
                "publicationDate": {
                    "$gt": start_date,
                    "$lt": end_date
                }
            }
        },
        {
            "$count": "paperCount"
        }
    ]
    paper_count = 0
    for result in collection.aggregate(pipeline, allowDiskUse=True):
        paper_count = result['paperCount']
    return paper_count


def get_authors_count(database, collection, mongo_host, mongo_port, start_year, start_month, end_year, end_month):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    start_date = datetime(start_year, start_month, 1, 0, 0, 0)
    end_date = datetime(end_year, end_month, 1, 0, 0, 0)
    pipeline = [
        {
            "$addFields": {
                "publicationDate": {
                    "$dateFromString": {
                        "dateString": "$firstPublicationDate",
                        "format": "%Y-%m-%dT%H:%M:%S"
                    }
                }
            }
        },
        {
            "$match": {
                "publicationDate": {
                    "$gt": start_date,
                    "$lt": end_date
                }
            }
        },
        {
            "$unwind": {
                "path": "$authorList"
            }
        },
        {
            "$project": {
                "firstPublicationDate": 1.0,
                "authorList.name": {
                    "$concat": [
                        {
                            "$toUpper": "$authorList.firstName"
                        },
                        " ",
                        {
                            "$toUpper": "$authorList.lastName"
                        }
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": 'hi',
                "authors": {
                    "$addToSet": "$authorList.name"
                }
            }
        },
        {
            "$unwind": {
                "path": "$authors"
            }
        },
        {
            "$count": "authorsCount"
        }
    ]
    authors_count = 0
    for result in collection.aggregate(pipeline, allowDiskUse=True):
        authors_count = result['authorsCount']
    return authors_count


def get_references_count(database, collection, mongo_host, mongo_port, start_year, start_month, end_year, end_month):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    start_date = datetime(start_year, start_month, 1, 0, 0, 0)
    end_date = datetime(end_year, end_month, 1, 0, 0, 0)
    pipeline = [
        {
            "$addFields": {
                "publicationDate": {
                    "$dateFromString": {
                        "dateString": "$firstPublicationDate",
                        "format": "%Y-%m-%dT%H:%M:%S"
                    }
                }
            }
        },
        {
            "$match": {
                "publicationDate": {
                    "$gt": start_date,
                    "$lt": end_date
                }
            }
        },
        {
            "$unwind": {
                "path": "$references"
            }
        },
        {
            "$project": {
                "references.id": {"$toUpper": "$references.id"}
            }
        },
        {
            "$group": {
                "_id": 'hi',
                "references": {
                    "$addToSet": "$references.id"
                }
            }
        },
        {
            "$unwind": {
                "path": "$references"
            }
        },
        {
            "$count": "referencesCount"
        }
    ]
    references_count = 0
    for result in collection.aggregate(pipeline, allowDiskUse=True):
        references_count = result['referencesCount']
    return references_count


def get_keywords_count(database, collection, mongo_host, mongo_port, start_year, start_month, end_year, end_month):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    start_date = datetime(start_year, start_month, 1, 0, 0, 0)
    end_date = datetime(end_year, end_month, 1, 0, 0, 0)
    pipeline = [
        {
            "$addFields": {
                "publicationDate": {
                    "$dateFromString": {
                        "dateString": "$firstPublicationDate",
                        "format": "%Y-%m-%dT%H:%M:%S"
                    }
                }
            }
        },
        {
            "$match": {
                "publicationDate": {
                    "$gt": start_date,
                    "$lt": end_date
                }
            }
        },
        {
            "$unwind": {
                "path": "$keywordList.keyword"
            }
        },
        {
            "$project": {
                "keywordList.keyword": {"$toUpper": "$keywordList.keyword"}
            }
        },
        {
            "$group": {
                "_id": 'hi',
                "keywords": {
                    "$addToSet": "$keywordList.keyword"
                }
            }
        },
        {
            "$unwind": {
                "path": "$keywords"
            }
        },
        {
            "$count": "keywordsCount"
        }
    ]
    keywords_count = 0
    for result in collection.aggregate(pipeline, allowDiskUse=True):
        keywords_count = result['keywordsCount']
    return keywords_count


def get_top_authors(database, collection, mongo_host, mongo_port, start_year, start_month, end_year, end_month):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    start_date = datetime(start_year, start_month, 1, 0, 0, 0)
    end_date = datetime(end_year, end_month, 1, 0, 0, 0)
    pipeline = [
        {
            "$addFields": {
                "publicationDate": {
                    "$dateFromString": {
                        "dateString": "$firstPublicationDate",
                        "format": "%Y-%m-%dT%H:%M:%S"
                    }
                }
            }
        },
        {
            "$match": {
                "publicationDate": {
                    "$gt": start_date,
                    "$lt": end_date
                }
            }
        },
        {
            "$unwind": {
                "path": "$authorList"
            }
        },
        {
            "$project": {
                "authorList.name": {
                    "$concat": [
                        {
                            "$toUpper": "$authorList.firstName"
                        },
                        " ",
                        {
                            "$toUpper": "$authorList.lastName"
                        }
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$authorList.name",
                "publications": {
                    "$addToSet": "$_id"
                }
            }
        },
        {
            "$match": {
                "_id": {
                    "$exists": True,
                    "$ne": " "
                }
            }
        },
        {
            "$unwind": {
                "path": "$publications"
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "publicationsCount": {
                    "$sum": 1.0
                }
            }
        },
        {
            "$sort": {
                "publicationsCount": -1.0
            }
        },
        {
            "$limit": 5.0
        }
    ]
    authors = []
    for result in collection.aggregate(pipeline, allowDiskUse=True):
        authors.append(dict(name=result['_id'], paperCount=result['publicationsCount']))
    return authors


def get_top_references(database, collection, mongo_host, mongo_port, start_year, start_month, end_year, end_month):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    start_date = datetime(start_year, start_month, 1, 0, 0, 0)
    end_date = datetime(end_year, end_month, 1, 0, 0, 0)
    pipeline = [
        {
            "$addFields": {
                "publicationDate": {
                    "$dateFromString": {
                        "dateString": "$firstPublicationDate",
                        "format": "%Y-%m-%dT%H:%M:%S"
                    }
                }
            }
        },
        {
            "$match": {
                "publicationDate": {
                    "$gt": start_date,
                    "$lt": end_date
                }
            }
        },
        {
            "$project": {
                "references.title": 1.0,
                "references.id": 1.0,
                "references.pubYear": 1.0,
                "references.source": 1.0,
                "references.authorString": 1,
            }
        },
        {
            "$unwind": {
                "path": "$references"
            }
        },
        {
            "$match": {
                "references.id": {
                    "$exists": True,
                    "$ne": None
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "id": "$references.id",
                    "source": "$references.source",
                    "title": "$references.title",
                    "year": "$references.pubYear",
                    "authors": "$references.authorString",
                },
                "citedBy": {
                    "$addToSet": "$_id"
                }
            }
        },
        {
            "$unwind": {
                "path": "$citedBy"
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "citationsCount": {
                    "$sum": 1.0
                }
            }
        },
        {
            "$sort": {
                "citationsCount": -1.0
            }
        },
        {
            "$limit": 100.0
        }
    ]
    references = []
    for result in collection.aggregate(pipeline, allowDiskUse=True):
        references.append(dict(id=result['_id']['id'],
                               source=result['_id']['source'],
                               title=result['_id']['title'],
                               year=result['_id']['year'],
                               authors=result['_id']['authors'],
                               citationsCount=result['citationsCount']))
    return references


def get_top_terms(database, collection, mongo_host, mongo_port, start_year, start_month, end_year, end_month):
    client = MongoClient(mongo_host, mongo_port)
    db = client[database]
    collection = db[collection]
    start_date = datetime(start_year, start_month, 1, 0, 0, 0)
    end_date = datetime(end_year, end_month, 1, 0, 0, 0)
    pipeline = [
        {
            "$addFields": {
                "publicationDate": {
                    "$dateFromString": {
                        "dateString": "$firstPublicationDate",
                        "format": "%Y-%m-%dT%H:%M:%S"
                    }
                }
            }
        },
        {
            "$match": {
                "publicationDate": {
                    "$gt": start_date,
                    "$lt": end_date
                }
            }
        },
        {
            "$project": {
                "annotations.prefLabel": 1.0,
                "annotations.ontology": 1.0,
                "annotations.id": 1.0
            }
        },
        {
            "$unwind": {
                "path": "$annotations"
            }
        },
        {
            "$match": {
                "annotations.ontology": "http://data.bioontology.org/ontologies/DOID"
            }
        },
        {
            "$group": {
                "_id": {
                    "label": "$annotations.prefLabel",
                    "link": "$annotations.id"
                },
                "usedBy": {
                    "$addToSet": "$_id"
                }
            }
        },
        {
            "$unwind": {
                "path": "$usedBy"
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "usedByCount": {
                    "$sum": 1.0
                }
            }
        },
        {
            "$sort": {
                "usedByCount": -1.0
            }
        },
        {
            "$limit": 10.0
        }
    ]
    terms = []
    for result in collection.aggregate(pipeline, allowDiskUse=True):
        terms.append(dict(
            label=result['_id']['label'],
            link=result['_id']['link'],
            usedByCount=result['usedByCount']
                               ))
    return terms
