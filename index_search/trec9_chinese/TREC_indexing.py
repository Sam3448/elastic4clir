from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup
import itertools
import codecs
import gzip
import os
import datetime
import requests
import configparser
import sys



#datadir="/Users/SamZhang/Documents/RA2017/src/dataset/TREC/trec9_chinese/docs" 
datadir='/Users/SamZhang/Documents/RA2017/src/dataset/TREC/trec9_chinese/docs'
configFile = str(sys.argv[1])

config = configparser.ConfigParser()
config.read(configFile)
docIndex = config['mapping']['index']
analyzer_name = config['mapping']['analyzer']
search_analyzer_name = config['mapping']['search_analyzer']
field1 = config['mapping']['field1']
field2 = config['mapping']['field2']
field3 = config['mapping']['field3']


# In[224]:


def index_document(docno, text, docid, es, docType):
    '''
    todo: submit docno,text pair to index via es.index()
    reference: https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/index.html
    '''
    res = text.split("\n")
    #es.index(index="trec", doc_type=docType, id=docid, body={"content":res})
    #Add doc number as ID instead of docid
    es.index(index=docIndex, doc_type=docType, id=docno, body={"content":res})


# In[203]:


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
                    docno = doc.find(field1).text.rstrip().lstrip()
                    text = doc.find(field2).text.rstrip().lstrip()
                    docid = doc.find(field3).text.rstrip().lstrip()
#                     if doc.find('headline'):
#                         headline = doc.find('headline').text.rstrip().lstrip()
#                     section = doc.find('section').text.rstrip().lstrip()#what if value is null?
#                     print str(count),docno,text.encode('utf-8')
                    count +=1
                    index_document(docno, text, docid, es, docType)
        except Exception as e:
            print ("Parsing error in %s: %s" % (filename, str(e)))
            return doc
    return count
    
es = Elasticsearch()
mapping = '''
{  
  "mappings":{  
    "TREC_HKCD":{  
        "properties": {
            "content": {
                "type": "text",
                "analyzer": %s,
                "search_analyzer": %s
            }
        }
    }
  }
}'''%(analyzer_name, search_analyzer_name)
#es.indices.delete(index='trec')
es.indices.create(index=docIndex, ignore=400, body=mapping)


# In[225]:


totalcount = 0
for dirname in os.listdir(datadir):
    if dirname[0] != '.':
        for filename in os.listdir(datadir + "/" + dirname):
            if filename.endswith('gz'):
                count = extract_documents(datadir + '/' + dirname + '/' + filename, dirname, es)
                totalcount += count
                print ("Indexed %s documents in %s (%d total documents so far)" %(count, dirname + "/" + filename, totalcount)) 

