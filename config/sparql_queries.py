queries = {
    'CO-AUTHORSHIP': """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX bibo: <http://purl.org/ontology/bibo/>
    PREFIX sio: <http://semanticscience.org/resource/>
    
    SELECT ?node1 ?node2 ?date (COUNT (DISTINCT ?paper) as ?weight){{
      {{
         SELECT ?paper ?title ?date {{
               ?paper sio:SIO_001278 ?dataset .
               ?paper dcterms:title ?title .
               ?paper dcterms:issued ?date .
               FILTER(?date >= "{start_year}-{start_month}-01T00:00:00"^^xsd:dateTime  && ?date < "{end_year}-{end_month}-01T00:00:00"^^xsd:dateTime)
         }}
      }}
      ?paper bibo:authorList ?authorList .
      ?authorList rdfs:member ?author1 .
      ?authorList rdfs:member ?author2 .
      ?author1 foaf:name ?node1 .
      ?author2 foaf:name ?node2 .
      FILTER(?author1 != ?author2)
    }} GROUP BY ?node1 ?node2 ?date
    """,
    'BURST': """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX sio: <http://semanticscience.org/resource/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX oa: <http://www.w3.org/ns/oa#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX doco: <http://purl.org/spar/doco/>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX bibo: <http://purl.org/ontology/bibo/>
    SELECT ?date ?title ?abstract (GROUP_CONCAT(DISTINCT ?annotation1Label;separator="|") AS ?annotations) {{
      ?paper sio:SIO_001278 ?dataset .
      ?paper dcterms:title ?title .
      ?paper bibo:abstract ?abstract .
      ?paper dcterms:issued ?date .
      ?annotation1 a oa:Annotation ;
                   oa:hasTarget ?paragraph ;
                   oa:hasBody ?ontoBody1 ;
                   oa:hasBody ?textualBody1 .
      ?textualBody1 a oa:TextualBody ;
                    rdf:value ?annotation1Label .
      ?paragraph oa:hasSource ?paper .
      FILTER(?date >= "{start}-01-01T00:00:00"^^xsd:dateTime  && ?date < "{end}-01-01T00:00:00"^^xsd:dateTime)
      FILTER(STRSTARTS(STR(?ontoBody1), "{ontology}"))
    }} GROUP BY ?date ?title ?abstract
    """,
    'PAPER_ANNOTATIONS': """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX sio: <http://semanticscience.org/resource/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX oa: <http://www.w3.org/ns/oa#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX luc: <http://www.ontotext.com/owlim/lucene#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX doco: <http://purl.org/spar/doco/>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX bibo: <http://purl.org/ontology/bibo/>
    SELECT ?date ?title (GROUP_CONCAT(DISTINCT ?annotation1Label;separator="|") AS ?annotations) {{
      {{
         SELECT ?paper ?title ?date {{
               ?paper sio:SIO_001278 ?dataset .
               ?paper dcterms:title ?title .
               ?paper dcterms:issued ?date .
               FILTER(?date >= "{start_year}-{start_month}-01T00:00:00"^^xsd:dateTime  && ?date < "{end_year}-{end_month}-01T00:00:00"^^xsd:dateTime)
         }}
      }}
      ?paragraph oa:hasSource ?paper .
      ?annotation1 a oa:Annotation ;
                   oa:hasTarget ?paragraph ;
                   oa:hasBody ?ontoBody1 ;
                   oa:hasBody ?textualBody1 .
      ?textualBody1 a oa:TextualBody ;
                    rdf:value ?annotation1Label .
      FILTER(STRSTARTS(STR(?ontoBody1), "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl"))
    }} GROUP BY ?date ?title ?abstract
    """,
    'CO-CITATION': """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX sio: <http://semanticscience.org/resource/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX oa: <http://www.w3.org/ns/oa#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX luc: <http://www.ontotext.com/owlim/lucene#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX doco: <http://purl.org/spar/doco/>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX bibo: <http://purl.org/ontology/bibo/>
    
    SELECT ?title1 ?title2 (COUNT (DISTINCT ?paper) as ?weight) {
      {
        SELECT ?paper {
          ?paper sio:SIO_001278 ?dataset .
          ?paper dcterms:issued ?date .
          FILTER(?date >= "{start}-01-01T00:00:00"^^xsd:dateTime  && ?date < "{end}-01-01T00:00:00"^^xsd:dateTime)
        }
      }
      ?paper bibo:cites ?citedPaper1 .
      ?paper bibo:cites ?citedPaper2 .
      ?citedPaper1 dcterms:title ?title1 .
      ?citedPaper2 dcterms:title ?title2 .
    } GROUP BY ?title1 ?title2
    """,
    'PAPER-CITATIONS': """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX sio: <http://semanticscience.org/resource/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX oa: <http://www.w3.org/ns/oa#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX luc: <http://www.ontotext.com/owlim/lucene#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX doco: <http://purl.org/spar/doco/>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX bibo: <http://purl.org/ontology/bibo/>
    
    SELECT ?date ?title (GROUP_CONCAT (DISTINCT ?citedPaper; separator="|") as ?references) {{
      {{
        SELECT ?date ?paper ?title {{
          ?paper sio:SIO_001278 ?dataset .
          ?paper dcterms:issued ?date .
          ?paper dcterms:title ?title .
          FILTER(?date >= "{start_year}-{start_month}-01T00:00:00"^^xsd:dateTime  && ?date < "{end_year}-{end_month}-01T00:00:00"^^xsd:dateTime)
        }}
      }}
      ?paper bibo:cites ?citedPaper .
      ?citedPaper a bibo:AcademicArticle .
    }} GROUP BY ?date ?title
    """

}