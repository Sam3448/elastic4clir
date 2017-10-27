from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup
import itertools
import codecs
import gzip
import os
import datetime
import sys


es = Elasticsearch()
keyWord = str(sys.argv[1])
response = es.search(index="trec", doc_type="HKCD",body = {    "query" : { "match" : { "content" : keyWord }},
    "highlight" : {
        "pre_tags" : ["<tag1>", "<tag2>"],
        "post_tags" : ["</tag1>", "</tag2>"],
        "fields" : {
            "content" : {}
        }
    }})

print (response)