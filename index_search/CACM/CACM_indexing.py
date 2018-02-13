from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup
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
datadir = config['mapping']['datadir']
docIndex = config['mapping']['index']
analyzer_name = config['mapping']['analyzer']
search_analyzer_name = config['mapping']['search_analyzer']
field1 = config['mapping']['field1']
field2 = config['mapping']['field2']
field3 = config['mapping']['field3']

# In[224]:


def index_document(title, text, docid, es):
    '''
    todo: submit docno,text pair to index via es.index()
    reference: https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/index.html
    '''
    docType = 'old'
    es.index(index=docIndex, doc_type=docType, id=docid, body={"title" : title, "content":text})


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
                if doc.find(field1) and doc.find(field2):
                    docid = doc.find(field1).text.rstrip().lstrip()
                    title = doc.find(field2).text.rstrip().lstrip()
                    abstract = ''
                    if doc.find(field3):
                        abstract = doc.find(field3).text.rstrip().lstrip()
                    print(title)
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
                "analyzer": %s,
                "search_analyzer": %s
            }
        }
    }
  }
}'''%(analyzer_name, search_analyzer_name)
es.indices.create(index=docIndex, ignore=400, body=mapping)


# In[225]:
totalcount = 0
count = extract_documents(datadir, es)
totalcount += count
print ("Indexed %s documents in %s (%d total documents so far)" %(count, datadir + "/" + datadir, totalcount)) 

