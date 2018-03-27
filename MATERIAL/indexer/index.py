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


def index_document(es, doc_id, doc_text):
    status = ''
    if not es.exists(index = docIndex, doc_type = docType, id = doc_id):
        es.index(index = docIndex, doc_type = docType, id = doc_id, body = {newField : doc_text})
        status='CREATING'
    else:
        es.update(index = docIndex, doc_type = docType, id = doc_id, body = {docType : {newField : doc_text}})
        status = 'UPDATING'

    return status


def extract_text(filename):

    text = []
    with codecs.open(filename) as filename_fid:
        for line in filename_fid:
            english_text = line.split('\t')[-1]
            text.append(english_text)
    return "".join(text)



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

print (es.indices.get_mapping(index = docIndex, doc_type = docType))

totalcount = 0

for datadir in datadirs:
    for filename in os.listdir(datadir):
        if filename.startswith('MATERIAL'):
            doc_id=filename.split('.')[0]
            
            #add it to <DatasetDocumentIDsFile>
            f_datasetDocIDs.write(doc_id + '\n')
            
            doc_text = extract_text(datadir+"/"+filename)
            status = index_document(es, doc_id, doc_text)
            totalcount += 1
            #print(doc_id,doc_text)
            print("%s ==> current file Number : %s ; %d "%(status, doc_id, totalcount))

f_datasetDocIDs.close()

