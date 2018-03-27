# elastic4clir
An ElasticSearch package for Cross-Lingual Information Retrieval

The goal of *elastic4clir* is to provide a flexible framework for running cross-lingual information retrieval (CLIR) experiments. It implements various retrieval techniques and benchmarks while using ElasticSearch/Lucene as the backend index and search components.


## Installation

First, clone this repo, and setup your conda environment:

   ```bash
   cd ~/your-working-directory
   git clone (this repo)
   cd elastic4clir
   conda env create -f conda-clir-env.yml
   source activate clir
   ```

Second, you need to get ElasticSearch separately. This version of elastic4clir is based on elasticsearch-5.6.3. Various version can be downloaded from: https://www.elastic.co/downloads/past-releases

   ```bash
   wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-5.6.3.tar.gz
   gunzip elasticsearch-5.6.3.tar
   tar -xvf elasticsearch-5.6.3.tar
   ```

That's it! To start the ElasticSearch server as a daemon,

   ```bash
   ./elasticsearch-5.6.3/bin/elasticsearch -d
   ```

To stop the ElasticSearch server,

   ```bash
   jps | grep Elasticsearch
   ```

Then kill the process with the PID. Note that the indices persist in the data directory of elasticsearch. To clean-up, you can just delete the directory. 

##

Under this directory:

* index_research: all scripts for indexing and searching. Right now two datasets are included: TREC and CACM.
  And now we have Wiki_sw dataset ready for indexing and searching. 

* evaluation: all evaluation scripts.

* web: for future development. (ignore it for now, just for test and fun)
 
## Runing an experiment (index, query, then evaluate)

