from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup
import itertools
import codecs
import gzip
import os
import datetime

datadir="/Users/SamZhang/Documents/RA2017/lucene4ir/data/cacm/cacm_form" 


# In[224]:


def index_document(title, text, docid, es):
    '''
    todo: submit docno,text pair to index via es.index()
    reference: https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/index.html
    '''
    docType = 'old'
    es.index(index="cacm", doc_type=docType, id=docid, body={"title" : title, "content":text})


# In[203]:


def extract_documents(filename, es):
    '''
    Extract documents and their contents from a single TREC file
    '''
    with open(filename) as cacmfile:
        soup = BeautifulSoup(cacmfile, "html.parser")
        print ('here')
        count = 0
        try:
            for doc in soup.find_all('doc'):
                if doc.find('doci') and doc.find('doct'):
                    docid = doc.find('doci').text.rstrip().lstrip()
                    title = doc.find('doct').text.rstrip().lstrip()
                    abstract = ''
                    if doc.find('docw'):
                        abstract = doc.find('docw').text.rstrip().lstrip()
                    print(docid)
                    print(abstract)
#                     if doc.find('headline'):
#                         headline = doc.find('headline').text.rstrip().lstrip()
#                     section = doc.find('section').text.rstrip().lstrip()#what if value is null?
#                     print str(count),docno,text.encode('utf-8')
                    count +=1
                    index_document(title, abstract, docid, es)
        except Exception as e:
            print ("Parsing error in %s: %s" % (filename, str(e)))
            return doc
    return count
    
es = Elasticsearch()
mapping = '''
{  
  "mappings":{  
    "old":{  
        "properties": {
            "title":{
                "type" : "string"
            },
            "content": {
                "type": "text",
                "analyzer": "standard",
                "search_analyzer": "standard"
            }
        }
    }
  }
}'''
es.indices.create(index='cacm', ignore=400, body=mapping)


# In[225]:
totalcount = 0
count = extract_documents(datadir, es)
totalcount += count
print ("Indexed %s documents in %s (%d total documents so far)" %(count, datadir + "/" + datadir, totalcount)) 
