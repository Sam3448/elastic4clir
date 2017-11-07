#!/usr/bin/env python

from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup
import itertools
import codecs
import gzip
import os

# set location of trec9 documents
datadir="/Users/SamZhang/Documents/RA2017/src/dataset/TREC/trec9_chinese/docs/HKCD/" 


def index_document(docno, text):
    '''
    todo: submit docno,text pair to index via es.index()
    reference: https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/index.html
    '''
    pass


def extract_documents(filename):
    '''
    Extract documents and their contents from a single TREC file
    '''
    with gzip.open(filename) as gzfile:
        soup = BeautifulSoup(gzfile)
        count = 0
        try:
            for doc in soup.find_all('doc'):
                if doc.find('docno') and doc.find('text'):
                    docno = doc.find('docno').text.rstrip().lstrip()
                    text = doc.find('text').text.rstrip().lstrip()
                    #print str(count),docno,text.encode('utf-8')
                    count +=1
                    index_document(docno, text)
        except Exception as e:
            print ("Parsing error in %s: %s" % (filename, str(e)))
            return doc
    return count




### MAIN LOOP
es = Elasticsearch()
totalcount = 0
for filename in os.listdir(datadir):
    if filename.endswith('gz'):
        count = extract_documents(datadir+'/'+filename)
        totalcount += count
        print ("Indexed %s documents in %s (%d total documents so far)" %(count, filename, totalcount))
