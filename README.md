# elastic4clir
ElasticSearch package for Cross-lingual Information Retrieval

## Installation & Setup

To setup the conda environment:

   conda env create -f conda-clir-env.yml
   source activate clir

This version of elastic4clir is based on elasticsearch-5.6.3. Download this from: https://www.elastic.co/downloads/past-releases and start up ElasticSearch before running the indexing/evaluation scripts. 

##

Under this directory:

* index_research: all scripts for indexing and searching. Right now two datasets are included: TREC and CACM.
  And now we have Wiki_sw dataset ready for indexing and searching. 

* evaluation: all evaluation scripts.

* web: for future development. (ignore it for now, just for test and fun)
 
## Runing an experiment (index, query, then evaluate)

