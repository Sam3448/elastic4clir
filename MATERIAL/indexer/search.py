from elasticsearch import Elasticsearch
import itertools
import codecs
import gzip
import os
import datetime
import sys
import json
import configparser


def search(index_name, fieldName, keyWord, num_results=5):
    es = Elasticsearch()

    fieldArr = []
    if "," in fieldName:
        fieldArr = fieldName.split(",")
        for i in range(len(fieldArr)):
            fieldArr[i] = fieldArr[i].strip()
    else:
        fieldArr.append(fieldName.strip())

    queryField = "\",\"".join(fieldArr)

    queryStr = '''{
        "query": {
            "query_string" : {
                "fields" : [\"%s\"],
                "query" : \"%s\"
            }
        }
    }'''%(queryField, keyWord)

    response = es.search(index=index_name, body = queryStr)

    return response

if __name__ == '__main__':
    USAGE = "python search.py <config-file> <query>"
    if len(sys.argv) != 3:
        print (USAGE)
        sys.exit()    
    
    configFile = str(sys.argv[1])
    config = configparser.ConfigParser()
    config.read(configFile)
    
    docIndex = config['Search']['index']
    fieldName =config['Search']['system_id']
    qry = str(sys.argv[2])
    res = search(docIndex, fieldName, qry)
    
    for each_doc in res['hits']['hits']:
        print(each_doc['_id'], each_doc['_score'])
    print (json.dumps(res, indent=4))
