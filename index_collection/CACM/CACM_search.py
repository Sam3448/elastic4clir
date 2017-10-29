from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup
import itertools
import codecs
import gzip
import os
import datetime
import sys
import json

def search(keyWord):
    es = Elasticsearch()
    #Removed Doc_type for Evaluation Metric
    #Also added size paramter as it defaults to 10
    response = es.search(index="cacm", body = { "size" : 100,   "query": {
    "bool": {
      "should": [
        { "match": { "content": keyWord } },
        { "match": { "title": keyWord } },
        { "match": { "author": keyWord } }
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
    USAGE = "python CACM_search.py <query>"
    if len(sys.argv) != 2:
        print (USAGE)
        sys.exit()
    
    res = search(str(sys.argv[1]))
    print (json.dumps(res, indent=4))
