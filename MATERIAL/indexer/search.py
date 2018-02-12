from elasticsearch import Elasticsearch
import itertools
import codecs
import gzip
import os
import datetime
import sys
import json
import configparser


def search(index_name, keyWord, num_results=5):
    es = Elasticsearch()
    #Removed Doc_type for Evaluation Metric
    #Also added size paramter as it defaults to 10
    response = es.search(index=index_name, body = { "size" : num_results,   "query": {
    "bool": {
      "should": [
        { "match": { "content": keyWord } }
      ]
    }
  },
        "highlight" : {
            "pre_tags" : ["<tag1>", "<tag2>"],
            "post_tags" : ["</tag1>", "</tag2>"],
            "fields" : {
                "content" : {}
            }
        }})
    return response

if __name__ == '__main__':
    USAGE = "python search.py <config-file> <query>"
    if len(sys.argv) != 3:
        print (USAGE)
        sys.exit()    
    
    configFile = str(sys.argv[1])
    config = configparser.ConfigParser()
    config.read(configFile)
    
    docIndex = config['Indexer']['index']
    qry = str(sys.argv[2])
    res = search(docIndex, qry)
    
    for each_doc in res['hits']['hits']:
        print(each_doc['_id'], each_doc['_score'])
    print (json.dumps(res, indent=4))
