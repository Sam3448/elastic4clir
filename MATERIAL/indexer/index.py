from elasticsearch import Elasticsearch
import itertools
import codecs
import gzip
import os
import datetime
import configparser
import sys

configFile = str(sys.argv[1])

config = configparser.ConfigParser()
config.read(configFile)

#Supports multiple data-directories
datadirs = [x.strip() for x in config['Indexer']['datadir'].split(',')]
docIndex = config['Indexer']['index'].strip()
docType = 'doc'
newField = config['Indexer']['system_id'].strip()
index_analyzer = config['Indexer']['analyzer'].strip()
search_analyzer = config['Indexer']['search_analyzer'].strip()
verbose = int(config['Indexer']['verbose'].strip())

def index_document(es, doc_id, doc_text):
    '''Index a document into ElasticSearch with id=doc_id and text=doc_text'''
    status = ''
    if not es.exists(index = docIndex, doc_type = docType, id = doc_id):
        es.index(index = docIndex, doc_type = docType, id = doc_id, body = {newField : doc_text})
        status='CREATING'
    else:
        es.update(index = docIndex, doc_type = docType, id = doc_id, body = {docType : {newField : doc_text}})
        status = 'UPDATING'

    return status


def extract_text(filename):
    '''Extract text from a file. Assumes we extract English text from final field'''
    text = []
    with codecs.open(filename) as filename_fid:
        for line in filename_fid:
            english_text = line.split('\t')[-1]
            text.append(english_text)
    return "".join(text)


########################
# Setup ElasticSearch
es = Elasticsearch()
if not es.indices.exists(index = docIndex):
    es.indices.create(index = docIndex)

mapping = '''{
  "properties": {
    \"%s\": {
      "type": "text",
      "analyzer": \"%s\",
      "search_analyzer": \"%s\"
    }
  }
}'''%(newField, index_analyzer, search_analyzer)

es.indices.put_mapping(index = docIndex, doc_type = docType, body = mapping)

########################
# Loop over files in datadirs and start indexing
totalcount = num_updates = num_created = 0
for datadir in datadirs:
    for filename in os.listdir(datadir):
        if filename.startswith('MATERIAL'):
            doc_id=filename.split('.')[0]
            doc_text = extract_text(datadir+"/"+filename)
            status = index_document(es, doc_id, doc_text)
            if status == 'CREATING':
                num_created += 1
            elif status == 'UPDATING':
                num_updates += 1
            totalcount += 1
            if verbose >= 1:
                print("%s ==> current file Number : %s ; %d "%(status, doc_id, totalcount))


print("Total %d docs created and %d docs updated in index %s" %(num_created, num_updates, docIndex))
if verbose >= 1:
    print("Current ElasticSearch mapping:")
    print(es.indices.get_mapping(index = docIndex, doc_type = docType))
                


