# Science Radar CLI
Prototype Command Line Client for automatic Research Front detection.
   - EuropePMC data harversting
   - PMC OA data downloading
   - XML2RDF transformation using Biotea
   - Semantic Annotation using Biotea
   - Automatic generation of co-authorship, co-citation and annotation co-occurrence networks
   - Automatic analysis of network metrics
   - Burst detection over titles, abstract, fulltext and annotations

## Requirements
   - Python 3.6+
   - Lxml
   - A SPARQL 1.1 compliance Triple Store (Apache Fuseki)

## Installation
```console
git clone https://github.com/ficolo/sciradar.git
cd sciradar
virtualenv -p python3 sciradar
source sciradar/bin/activate
pip install -r requirements.txt
```
## Execution

## Docker container 