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
datadir = config['Indexer']['datadir']
docIndex = config['Indexer']['index']
analyzer_name = config['Indexer']['analyzer']
search_analyzer_name = config['Indexer']['search_analyzer']
system_id = config['Indexer']['system_id']



def index_document(es, doc_id, doc_text):
    '''
    reference: https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/index.html
    '''
    es.index(index=docIndex, doc_type='mydoc', id=doc_id, body={"doc_id" : doc_id, "content":doc_text})


def extract_text(filename):
    text = []
    with codecs.open(filename) as filename_fid:
        for line in filename_fid:
            english_text = line.split('\t')[-1]
            text.append(english_text)
    return "".join(text)
    #return text[0]



es = Elasticsearch()
mapping = '''
{  
  "mappings":{  
    "mydoc":{  
        "properties": {
            "doc_id":{
                "type" : "string",
                "index" : "not_analyzed"
            },
            "content": {
                "type": "text",
                "analyzer": %s,
                "search_analyzer": %s
            }
        }
    }
  }
}'''%(analyzer_name, search_analyzer_name)
es.indices.create(index=docIndex, ignore=400, body=mapping)


totalcount = 0
for filename in os.listdir(datadir):
    if filename.startswith('MATERIAL'):
        doc_id=filename.split('.')[0]
        doc_text = extract_text(datadir+"/"+filename)
        index_document(es, doc_id, doc_text)
        print(doc_id,doc_text)
        totalcount += 1
    #if totalcount > 100:
    #    break    

print ("Indexed %s documents in %s (%d total documents so far)" %(totalcount, datadir, totalcount)) 

