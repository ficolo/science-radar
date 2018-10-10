class Publication:
    def __init__(self, publication_id, date, title, abstract='', annotations=[], references=[], authors=[]):
        self.publication_id = publication_id
        self.date = date
        self.title = title
        self.abstract = abstract
        self.annotations = annotations
        self.references = references
        self.authors = authors

    def __str__(self):
        return 'Publication(title="{}", date="{}")'.format(self.title, self.date)

    def to_dict(self):
        return {
            'date': self.date,
            'title': self.title,
            'abstract': self.abstract,
            'authors': self.authors,
            'annotations': self.annotations,
            'references': self.references
        }
