from django.http import HttpResponse

from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup
import itertools
import codecs
import gzip
import os
import datetime

def index(request):
    datadir = "/Users/SamZhang/Documents/RA2017/src/dataset/TREC/trec9_chinese/docs"
    es = Elasticsearch()
    mapping = '''
    {  
      "mappings":{  
        "TREC_HKCD":{  
            "properties": {
                "content": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_max_word"
                }
            }
        }
      }
    }'''
    es.indices.create(index='trec', ignore=400, body=mapping)
    totalcount = 0
    for dirname in os.listdir(datadir):
        if dirname[0] != '.':
            for filename in os.listdir(datadir + "/" + dirname):
                if filename.endswith('gz'):
                    count = extract_documents(datadir + '/' + dirname + '/' + filename, dirname, es)
                    totalcount += count
    return HttpResponse("Done")

def search(request):
    es = Elasticsearch()
    #keyWord = '1'
    ESresponse = es.search(index="trec", doc_type="HKCD", body={"query": {"match": {"content": "中"}},
                                                              "highlight": {
                                                                  "pre_tags": ["<tag1>", "<tag2>"],
                                                                  "post_tags": ["</tag1>", "</tag2>"],
                                                                  "fields": {
                                                                      "content": {}
                                                                  }
                                                              }})

    return HttpResponse(ESresponse)


def index_document(docno, text, docid, es, docType):
    '''
    todo: submit docno,text pair to index via es.index()
    reference: https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/index.html
    '''
    res = text.split("\n")
    es.index(index="trec", doc_type=docType, id=docid, body={"content":res})


def extract_documents(filename, docType, es):
    '''
    Extract documents and their contents from a single TREC file
    '''
    with gzip.open(filename) as gzfile:
        soup = BeautifulSoup(gzfile, "html.parser")
        count = 0
        try:
            for doc in soup.find_all('doc'):
                if doc.find('docno') and doc.find('text'):
                    docno = doc.find('docno').text.rstrip().lstrip()
                    text = doc.find('text').text.rstrip().lstrip()
                    docid = doc.find('docid').text.rstrip().lstrip()
#                     if doc.find('headline'):
#                         headline = doc.find('headline').text.rstrip().lstrip()
#                     section = doc.find('section').text.rstrip().lstrip()#what if value is null?
#                     print str(count),docno,text.encode('utf-8')
                    count +=1
                    print (docType)
                    index_document(docno, text, docid, es, docType)
        except Exception as e:
            print ("Parsing error in %s: %s" % (filename, str(e)))
            return doc
    return count
