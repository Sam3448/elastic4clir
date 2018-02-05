import matplotlib
matplotlib.use('Agg')
import sys
import os
import re
import subprocess
import collections
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import json
import importlib
from configparser import SafeConfigParser
from collections import OrderedDict
from elasticsearch import Elasticsearch
import re

def parse_query(query_string):
    conjunction = query_string.split(',')
    q = ""
    for c in conjunction:
        c2 = c.replace('EXAMPLE_OF(','').replace(')','').replace('"','').replace('+','').replace('<','').replace('>','')
        c3 = c2.split('[')[0]
        q+= c3 + " "
    return q

    #Given a query file, it maps the query number to the query
def get_queries(query_file):
    if not os.path.isfile(query_file) or os.stat(query_file).st_size == 0:
        return None
    
    query_dict = {}
    
    with open(query_file, 'r') as f:
        f.readline()
        for idx,cur_line in enumerate(f):
            query_id, query_string, domain_id = cur_line.split('\t')
            query_dict[query_id] = query_string
            query_string2 = parse_query(query_string)
            print(query_id, query_string,"->", query_string2)

    return query_dict

    
if __name__ == '__main__':
    USAGE = '\nUSAGE : python 1A_eval.py <config-file> \n'
    
    if len(sys.argv) != 2:
        print (USAGE)
        sys.exit()
    
    parser = SafeConfigParser({'output_path' : os.getcwd()})
    parser.read(sys.argv[1])
    
    if not (parser.has_option('Evaluation', 'query_file')):
        print ("Invalid/Incomplete Evaluation parameters in config file")
        sys.exit()

    query_file = parser.get('Evaluation', 'query_file')
    
    get_queries(query_file)

