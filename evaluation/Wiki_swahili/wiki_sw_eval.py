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
import numpy as np

# def computeROC(search_out,  ref_out, theta):
#     total_score = 0.0
#     total_count = 0
#     total_miss = 0.0
#     total_FA = 0.0
# 
#     for qry in search_out:
#         if qry not in ref_out:
#             continue 
#         else:
#             ref_docs = ref_out[qry]
#             search_docs = search_out[qry].keys()
#             search_docs = (tmp for tmp in search_docs and search_out[qry][tmp] > theta)
#             N_miss = len(ref_docs - search_docs) 
#             N_FA = len(search_docs - ref_docs)
#             N_relevant = len(ref_docs)
#             
#             #Might be duplicates from above but computing the confusion matrix again for clarity
#             TP = len((x for x in ref_docs and x in search_docs))
#             FN = len((x for x in ref_docs and x not in search_docs))
#             FP = len((x for x not in ref_docs and x in search_docs))
#             TN = len((x for x not in ref_docs  and x ))
#             P_miss = N_miss * 1.0/N_relevant
#             P_FA = N_FA * 1.0/(N_total - N_relevant)
# 
#             scores[qry] = 1.0 - (P_miss + beta * P_FA)
#             
#             total_score += scores[qry]
#             total_count +=1
#             total_miss += P_miss
#             total_FA += P_FA


#Implements the AQWV metric
def AQWV(ref_file, out_file, es_index, docs_per_qry=100):
    
    #Populate the reference outputs
    ref_out = {}
    with open(ref_file, 'r') as f_ref:
        for cur_line in f_ref:
            toks = cur_line.strip().split()
            assert len(toks) == 4
            
            q_id = toks[0]; doc_id = toks[2]; rel = int(toks[3]);
            if rel > 0:
                if q_id not in ref_out:
                    ref_out[q_id] = set()
                ref_out[q_id].add(doc_id)
    
    #Populate the search_output
    search_out = {}
    with open(out_file, 'r') as f_out:
        for cur_line in f_out:
            toks = cur_line.strip().split()
            assert len(toks) == 6
            
            q_id = toks[0]; doc_id = toks[2]; sim = float(toks[4]);
            if q_id not in search_out:
                search_out[q_id] = OrderedDict()
            search_out[q_id][doc_id] = sim
        
        #For each query , sort the documents acc. to  similarity
        #Prune it till it is docs_per_qry
        for q in search_out:
            search_out[q] = OrderedDict(sorted(search_out[q].items(), key = lambda x:x[1], reverse = True))

            #Prune till docs_per_qry
            if len(search_out[q]) > docs_per_qry :
                search_out[q] = OrderedDict(list(search_out[q].items())[0:docs_per_qry])
        

    #Count the number of documents
    es = Elasticsearch()
    r = es.search(index = es_index, body = {'size' : '0', 'query' : {}})
    N_total = int(r['hits']['total'])
    #print (N_total)
   
    #Define AQWV parameters
    C = 0.0333
    V = 1.0
    P_relevant = 1.0/600
    #Beta can be computed from the above quanties. But for CLIR, it is set to 20.0 
    #IMP : Need to see the use of theta 
    beta = 20.0
    theta = 0.0
    
    #Compute AQWV scores for each query 
    # IMP : For queries not present in both search_out and ref_out, AQWV is not computed
    scores = {}
    total_score = 0.0
    total_count = 0
    total_miss = 0.0
    total_FA = 0.0

    for qry in search_out:
        if qry not in ref_out:
            continue 
        else:
            ref_docs = ref_out[qry]
            search_docs = search_out[qry].keys()
            
            N_miss = len(ref_docs - search_docs) 
            N_FA = len(search_docs - ref_docs)
            N_relevant = len(ref_docs)
            
            P_miss = N_miss * 1.0/N_relevant
            P_FA = N_FA * 1.0/(N_total - N_relevant)

            scores[qry] = 1.0 - (P_miss + beta * P_FA)
            
            total_score += scores[qry]
            total_count +=1
            total_miss += P_miss
            total_FA += P_FA

            #print (qry, N_miss, N_FA, N_relevant, P_miss, P_FA, scores[qry])
    print ("For docs ", docs_per_qry, " AQWV is ", total_score/total_count, "P_Miss ", str(total_miss/total_count), " P_FA ", str(total_FA/total_count))
    

#Given a query file, it maps the query number to the query
def get_queries(query_file):
    if not os.path.isfile(query_file) or os.stat(query_file).st_size == 0:
        return None
    
    query_dict = {}
    
    with open(query_file, 'r') as f:
        for idx,cur_line in enumerate(f):
            toks = cur_line.strip().split(maxsplit=1)
            if len(toks) != 2:
                print("Invalid formatting in query_file at line ",idx+1)
            
            query_dict[int(toks[0])] = toks[1]
            
    return query_dict

#Runs evaluation given queries, gold output and our output.
#Returns the path to result file

def prec_recall_graph(output_path, FIN_OUT):
    with open(FIN_OUT , 'r') as f:
        MAP = 0
        prec = [0]*11
        idx = 0
        for line in f:
            toks = line.strip().split()
            if len(toks) == 3:
                if toks[0] == 'map':
                    MAP = float(toks[2])
                if 'iprec_at_recall_' in toks[0]:
                    prec[idx] = float(toks[2])
                    idx += 1
        assert idx == 11
        #print(MAP)
        #print (prec)
        plt.plot([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], prec)
        plt.plot([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], [MAP]*11)
        plt.ylabel("Precison")
        plt.xlabel("Recall")
        plt.title("Precison-Recall Curve")
        plt.annotate('Mean Average Precision\n(MAP) = '+ str(MAP), xy=(0.4, MAP), xytext=(0.6, max(prec)/3),\
            arrowprops=dict(facecolor='black', shrink=0.05),\
            )
        plt.savefig(os.path.join(output_path, "P-r-graph_wiki_swahili.png"))


def eval(query_file, ref_out_file, output_path, TREC_PATH, search, es_index, results_per_query):
    #File to store search output
    SEARCH_OUT = os.path.join(output_path, "search_output_wiki_swahili.txt")
    f_out = open(SEARCH_OUT,'w')
 
    #File to store output for Neural_network
    NN_IN = os.path.join(output_path, "nn_output_wiki_swahili.txt")
    f_nn = open(NN_IN, 'w')
    NN_q_d = []
 
    queries = get_queries(query_file)
 
    if queries is None or len(queries) == 0:
        print ("\nInvalid or Bad Query File. Exiting Evaluation module\n")
        sys.exit
     
    for q_num in queries:
        q_string =  queries[q_num]
 
        #Replace tabs with spaces as tab is delimited for shota's code
        q_string = q_string.replace('\t', ' ')
 
        res = search(q_string, results_per_query)
        for each_doc in res['hits']['hits']:
            f_out.write(str(q_num) + " " + "1" + " " + each_doc['_id'] + " " + "-1" + " " + str(each_doc['_score']) + " " + "STANDARD" + "\n")
 
            #Add query_id and doc_id to NN_q_d
            NN_q_d.append((int(q_num), int(each_doc['_id'])))
 
            #Add data to NN_out
            f_nn.write('qid=' + str(q_num) + '\t' + \
                        '-1' + '\t' + \
                        q_string + '\t' + \
                        each_doc['_source']['content'] + '\n')
 
    f_out.close()
    f_nn.close()
 
    #Saving query_document mapping to expand the Neural_net output
    np.save('q_d_num.npy', np.array(NN_q_d))
 
     
 
    print ("\nDone writing search_out and nn_out, running TREC_eval and AQWV\n")
     
    #Compile (make) the trec-eval code
    my_cwd = os.getcwd()
    os.chdir(TREC_PATH)
    subprocess.call(['make'])
    os.chdir(my_cwd)
     
    AQWV(ref_out_file, SEARCH_OUT, es_index)
 
    #Run it on Shota's output
    NN_OUT = '/export/a10/CLIR/neural_CLIR/fin_nn_scores.txt'
    AQWV(ref_out_file, NN_OUT, es_index, results_per_query)
#     AQWV(ref_out_file, NN_OUT, es_index, 190)
#     AQWV(ref_out_file, NN_OUT, es_index, 180)
#     AQWV(ref_out_file, NN_OUT, es_index, 170)
#     AQWV(ref_out_file, NN_OUT, es_index, 160)
#     AQWV(ref_out_file, NN_OUT, es_index, 150)
#     AQWV(ref_out_file, NN_OUT, es_index, 140)
#     AQWV(ref_out_file, NN_OUT, es_index, 130)
#     AQWV(ref_out_file, NN_OUT, es_index, 120)
#     AQWV(ref_out_file, NN_OUT, es_index, 110)
#     AQWV(ref_out_file, NN_OUT, es_index, 100)
#     AQWV(ref_out_file, NN_OUT, es_index, 90)
#     AQWV(ref_out_file, NN_OUT, es_index, 80)
#     AQWV(ref_out_file, NN_OUT, es_index, 70)
#     AQWV(ref_out_file, NN_OUT, es_index, 60)
#     AQWV(ref_out_file, NN_OUT, es_index, 50)
#     AQWV(ref_out_file, NN_OUT, es_index, 40)
#     AQWV(ref_out_file, NN_OUT, es_index, 30)
#     AQWV(ref_out_file, NN_OUT, es_index, 20)
#     AQWV(ref_out_file, NN_OUT, es_index, 10)

    #Run trec-eval
    TREC_EXEC = os.path.join(TREC_PATH,'trec_eval')
    if not os.path.isfile(TREC_EXEC):
        print ("\nFailed to find ",TREC_EXEC)
        sys.exit
    
    #File to store final output
    FIN_OUT = os.path.join(output_path, "results_wiki_swahili.txt")
    fin_out = open(FIN_OUT, 'w')
    print (subprocess.list2cmdline([TREC_EXEC, ref_out_file, SEARCH_OUT]))
    subprocess.call([TREC_EXEC, ref_out_file, SEARCH_OUT], stdout = fin_out)
    fin_out.close()
    prec_recall_graph(output_path, FIN_OUT)
    return FIN_OUT
    

if __name__ == '__main__':
    USAGE = '\nUSAGE : python wiki_sw_eval.py <config-file> \n'
    
    if len(sys.argv) != 2:
        print (USAGE)
        sys.exit()
    
    parser = SafeConfigParser({'output_path' : os.getcwd()})
    parser.read(sys.argv[1])
    
    if not (parser.has_option('Evaluation', 'search_script') or 
            parser.has_option('Evaluation', 'trec_eval_path') or
            parser.has_option('Evaluation', 'query_file') or
            parser.has_option('Evaluation', 'reference_file')or
            parser.has_option("Evaluation", 'index_name')):
        print ("Invalid/Incomplete Evaluation parameters in config file")
        sys.exit()

    search_script = parser.get('Evaluation', 'search_script')
    TREC_PATH = parser.get('Evaluation', 'trec_eval_path')
    query_file = parser.get('Evaluation', 'query_file')
    reference_file = parser.get('Evaluation', 'reference_file')
    output_path = parser.get('Evaluation', 'output_path')
    es_index = parser.get('Evaluation', 'index_name')
    
    #Import search module
    search_dir, search_file = os.path.split(search_script)
    if search_dir != '':
        sys.path.append(search_dir)
        #print (sys.path)
    if search_file == '':
        print ("Invalid search_script provided in Evaluation config")
        sys.exit()
    else:
        mod = importlib.import_module(search_file.replace('.py', ''))
        search_func = getattr(mod, 'search')   
    
    #results_per_query determines number of search results to return per query
    results_per_query=200
    eval(query_file, reference_file, output_path, TREC_PATH, search_func, es_index, results_per_query)
