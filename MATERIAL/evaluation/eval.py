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
import matplotlib.pyplot as plt
import math

#Hardcoding the path to official implementation of material scoring. Need to change in later
MATERIAL_EVAL_PATH = '/export/a10/CLIR/tmp/MATERIAL_tools-0.4.2'

#Checks all possible max_hits and finds the best AQWV overall
def best_score(ref_out, search_out, beta, max_hits, N_total, out_path):
    #Upper bound max_hits to num docs  indexed
    max_hits = min(max_hits, N_total)
    
    print ("Running AQWV between max_hits of", str(0), "to", str(max_hits))
    #This is the worst possible score
    best_AQWV = -beta
    best_hits = 0
    
    #(Debug) For drawing a graph
    hits = []
    AQWV_scores = []
    
    for cur_hits in range(0, max_hits+1):
        scores = {}
        total_score = 0.0
        total_count = 0
        
        # IMP : For queries not present in both search_out and ref_out, AQWV is not computed
        for qry in search_out:
            if qry not in ref_out:
                continue 
            else:
                ref_docs = ref_out[qry]
                search_docs = set( list( search_out[qry].keys() )[0:cur_hits+1] )
                
                N_miss = len(ref_docs - search_docs) 
                N_FA = len(search_docs - ref_docs)
                N_relevant = len(ref_docs)
                
                P_miss = N_miss * 1.0/N_relevant
                P_FA = N_FA * 1.0/(N_total - N_relevant)
    
                scores[qry] = 1.0 - (P_miss + beta * P_FA)
                
                total_score += scores[qry]
                total_count +=1
    
        cur_AQWV = total_score/total_count
        
        
        AQWV_scores.append(cur_AQWV)
        hits.append(cur_hits)
        
        if cur_AQWV > best_AQWV:
            best_AQWV = cur_AQWV
            best_hits = cur_hits
    
    #Create  a graph for debug purposes
    plt.plot(hits, AQWV_scores)
    plt.xlabel("max_hits"); plt.ylabel("AQWV score")
    plt.savefig(os.path.join(out_path, 'AQWV_trend.png'))
    
    return best_AQWV, best_hits

#Checks all possible max_hits and finds the best AQWV PER QUERY
def best_score_per_qry(ref_out, search_out, beta, max_hits, N_total, out_path):
    
    #Upper bound max_hits to num docs  indexed
    max_hits = min(max_hits, N_total)
    scores = {}
    total_score = 0.0
    total_count = 0
            
    # IMP : For queries not present in both search_out and ref_out, AQWV is not computed
    for qry in search_out:
        if qry not in ref_out:
            continue 
        else:
            best_AQWV = -beta
            for cur_hits in range(0, max_hits+1):
                
                ref_docs = ref_out[qry]
                search_docs = set( list( search_out[qry].keys() )[0:cur_hits+1] )
                
                N_miss = len(ref_docs - search_docs) 
                N_FA = len(search_docs - ref_docs)
                N_relevant = len(ref_docs)
                
                P_miss = N_miss * 1.0/N_relevant
                P_FA = N_FA * 1.0/(N_total - N_relevant)
    
                scores[qry] = 1.0 - (P_miss + beta * P_FA)
                if scores[qry] > best_AQWV:
                    best_AQWV = scores[qry]
                
            total_score += best_AQWV
            total_count +=1
    
    cur_AQWV = total_score/total_count
        
    return cur_AQWV



#Implements the AQWV metric
def AQWV(ref_file, out_file, es_index, max_hits):
    
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
        for q in search_out:
            search_out[q] = OrderedDict(sorted(search_out[q].items(), key = lambda x:x[1], reverse = True))
        

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
    
    #score, hits = best_score(ref_out, search_out, beta, max_hits, N_total, os.path.split(out_file)[0])
    score = best_score_per_qry(ref_out, search_out, beta, max_hits, N_total, os.path.split(out_file)[0])
    print ("Oracle QWV of", str(score))    
    
    #Computing AQWV for given max-hits
    scores = {}
    total_score = 0.0
    total_count = 0
    
    # IMP : For queries not present in both search_out and ref_out, AQWV is not computed
    for qry in search_out:
        if qry not in ref_out:
            continue 
        else:
            ref_docs = ref_out[qry]
            search_docs = ( search_out[qry].keys() )
            
            N_miss = len(ref_docs - search_docs) 
            N_FA = len(search_docs - ref_docs)
            N_relevant = len(ref_docs)
            
            P_miss = N_miss * 1.0/N_relevant
            P_FA = N_FA * 1.0/(N_total - N_relevant)

            scores[qry] = 1.0 - (P_miss + beta * P_FA)
            
            total_score += scores[qry]
            total_count +=1

    cur_AQWV = total_score/total_count
    print ("AQWV for max_hits of ", str(max_hits),"is", str(cur_AQWV))
    

def parse_query(query_string):
    '''very basic query parser'''
    conjunction = query_string.split(',')
    q = ""
    for c in conjunction:
        c2 = c.replace('EXAMPLE_OF(','').replace(')','').replace('"','').replace('+','').replace('<','').replace('>','')
        c3 = c2.split('[')[0]
        q+= c3 + " "
    return q
    
#Given a query file, it maps the query number to the query
domain_id2name = {
    'GOV':'Government-And-Politics',
    'LIF':'Lifestyle'
}

def get_queries(query_file):
    if not os.path.isfile(query_file) or os.stat(query_file).st_size == 0:
        return None
    
    query_dict = {}
    with open(query_file, 'r') as f:
        f.readline()
        for idx,cur_line in enumerate(f):
            query_id, query_string, domain_id, = cur_line.rstrip().split('\t')[0:3]
            query_dict[query_id] = {}
            query_dict[query_id]['parsed'] = parse_query(query_string)
            query_dict[query_id]['original'] = query_string + ":" + domain_id2name[domain_id]
            
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
        plt.savefig(os.path.join(output_path, "P-r-graph.png"))

#Normalize the similarity scores such that they are between 0 and 1
#Some times scores can be negative. So we add all scores by min and then normalize by sum
def normalize_scores(res):
    count = 0
    min_score = float("inf")
    tot_score = 0.0
    
    for each_doc in res['hits']['hits']:
        each_score = float(each_doc['_score'])
        count += 1
        tot_score += each_score
        if each_score < min_score:
            min_score = each_score

    tot_score += count * min_score
    for each_doc in res['hits']['hits']:
        each_doc['_score'] = (float(each_doc['_score']) + min_score)/tot_score

    
def create_AnswerKeyFile(base_out_folder, dataset_name, ref_file, queries):
    
    #Create a sub-directory for Reference
    out_folder = os.path.join(base_out_folder, 'Reference')
    
    if not os.path.exists(out_folder):
        os.mkdir(out_folder)
    
    ref_out = {}
    with open(ref_file, 'r') as f_ref:
        for cur_line in f_ref:
            toks = cur_line.strip().split()
            assert len(toks) == 4
            
            q_id = toks[0]; doc_id = toks[2]; rel = int(toks[3])
            if rel > 0:
                if q_id not in ref_out:
                    ref_out[q_id] = set()
                ref_out[q_id].add(doc_id)
    
    for qry in ref_out:
        with open(os.path.join(out_folder, dataset_name + 'q-' + qry + '.tsv'), 'w') as f_qry:
            f_qry.write(qry + '\t' + queries[qry]['original'] + '\n')
            for rel_docs in ref_out[qry]:
                f_qry.write(rel_docs + '\n')
    
    #Create subdirectory for generatedinputfiles
    gen_out_folder = os.path.join(base_out_folder, 'GeneratedInputFiles')
    if not os.path.exists(gen_out_folder):
        os.mkdir(gen_out_folder)

    #Create a subdirectory for scoredQWV files
    score_out_folder = os.path.join(base_out_folder, 'QueryScores')
    if not os.path.exists(score_out_folder):
        os.mkdir(score_out_folder)
    
    path_to_doc_file = os.path.join(base_out_folder, dataset_name + 'AllDocIDs.tsv')
    path_to_query_files = os.path.join(base_out_folder, 'SystemOutputFiles')
    path_to_ref_files = os.path.join(base_out_folder, 'Reference')
    material_validator = os.path.join(MATERIAL_EVAL_PATH, 'material_validator.py')
    material_scorer = os.path.join(MATERIAL_EVAL_PATH, 'material_scorer.py')

    print ('Calling Material Validator to create <GeneratedInputFiles>...')
    print ('Calling Material scorer to create QWV score for each query...')
    #Generate generatedinputfiles for each query in ref_out and in search out
    #Default condition is query must be present in both ref and search
    for qry in ref_out:
        if qry in queries:
            qry_file = os.path.join(path_to_query_files, 'q-' + qry + '.tsv')
            ref_file = os.path.join(path_to_ref_files, dataset_name + 'q-' + qry + '.tsv')
            gen_file = os.path.join(gen_out_folder, 'q-' + qry + '.ScoringReady.tsv')
            score_file = os.path.join(score_out_folder, 'q-' + qry + '.AQWVscores.tsv')

            val_command = material_validator + ' -s ' + qry_file + ' -d ' + path_to_doc_file + ' -r ' + ref_file + ' -g ' + gen_file
            
            #Add beta for customization
            score_command = material_scorer + ' -g ' + gen_file + ' -w ' + score_file            
            subprocess.call(val_command, shell=True)            
            
            subprocess.call(score_command, shell=True)
    
    #Generate final AQWV score
    fin_score_command = material_scorer + ' -m ' + score_out_folder + ' -w ' + os.path.join(base_out_folder, 'FinalAWQVscore.txt')
    print ('Calculating global AQWV score ..')
    subprocess.call(fin_score_command, shell=True)
    print ('FINISHED! Official AQWV score at ' + os.path.join(base_out_folder, 'FinalAWQVscore.txt') )



def eval(query_file, ref_out_file, output_path, TREC_PATH, search, es_index, system_id, dataset_name, max_hits):
    #Create output_path if it doesn't exist
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    
    #Generate list of documents (for NIST script)
    with open(os.path.join(output_path, dataset_name + '_CLIR_AllDocIDs.tsv'), 'w') as f_datasetDocIDs:
        f_datasetDocIDs.write(dataset_name + '\n')
        es = Elasticsearch()
        r = es.search(index = es_index, body = {'query': {'match_all': {}}}, filter_path=['hits.hits._id'], size = 10000)
        for d in r['hits']['hits']:
            f_datasetDocIDs.write(d['_id'] + '\n')
    
    #File to store search output
    SEARCH_OUT = os.path.join(output_path, "search_output.txt")

    #File to store <SystemOutputFiles> of every query
    SYSTEM_OUT_FILES = os.path.join(output_path, "SystemOutputFiles")
    if not os.path.exists(SYSTEM_OUT_FILES):
        os.mkdir(SYSTEM_OUT_FILES)

    f_out = open(SEARCH_OUT,'w')
    queries = get_queries(query_file)

    if queries is None or len(queries) == 0:
        print ("\nInvalid or Bad Query File. Exiting Evaluation module\n")
        sys.exit
    for q_num in queries:  
        q_string =  queries[q_num]['parsed']

        #Create a query file for this qID
        with open(os.path.join(SYSTEM_OUT_FILES, 'q-' + str(q_num) + '.tsv'), 'w') as f:
            f.write(str(q_num) + '\t' + queries[q_num]['original'] + '\n')
        
            res = search(es_index, system_id, q_string, max_hits) 
            if int(res['hits']['total']) == 0:
                f_out.write(str(q_num) + " " + "1 NO_HIT -1 1.0 STANDARD\n")
            else:
                normalize_scores(res)
                for each_doc in res['hits']['hits']:
                    f_out.write(str(q_num) + " " + "1" + " " + each_doc['_id'] + " " + "-1" + " " + str(each_doc['_score']) + " " + "STANDARD" + "\n")
                    f.write(each_doc['_id'] + '\t' + "{0:.3f}".format(each_doc['_score']) + '\n')

    
    #Create <answerkeyfile> , default setting task to CLIR
    dataset_name += '_CLIR_'
    create_AnswerKeyFile(output_path, dataset_name, ref_out_file, queries)


    
    f_out.close()
        
    AQWV(ref_out_file, SEARCH_OUT, es_index, max_hits)
    
    #Run trec-eval
    # TREC_EXEC = os.path.join(TREC_PATH,'trec_eval')
    # if not os.path.isfile(TREC_EXEC):
    #     print ("\nFailed to find ",TREC_EXEC)
    #     sys.exit
    
    # #File to store final output
    # FIN_OUT = os.path.join(output_path, "results.txt")
    # fin_out = open(FIN_OUT, 'w')
    # print (subprocess.list2cmdline([TREC_EXEC, ref_out_file, SEARCH_OUT]))
    # subprocess.call([TREC_EXEC, ref_out_file, SEARCH_OUT], stdout = fin_out)
    # fin_out.close()
    # prec_recall_graph(output_path, FIN_OUT)
    # return FIN_OUT


if __name__ == '__main__':
    USAGE = '\nUSAGE : python eval.py <config-file> \n'
    
    if len(sys.argv) != 2:
        print (USAGE)
        sys.exit()
    
    parser = SafeConfigParser({'output_path' : os.getcwd()})
    parser.read(sys.argv[1])
    
    if not (parser.has_option('Evaluation', 'search_script') or 
            parser.has_option('Evaluation', 'trec_eval_path') or
            parser.has_option('Evaluation', 'query_file') or
            parser.has_option('Evaluation', 'reference_file') or
            parser.has_option('Evaluation', 'system_id') or
            parser.has_option("Indexer", 'index')):
        print ("Invalid/Incomplete Evaluation parameters in config file")
        sys.exit()

    search_script = parser.get('Evaluation', 'search_script')
    TREC_PATH = parser.get('Evaluation', 'trec_eval_path')
    query_file = parser.get('Evaluation', 'query_file')
    reference_file = parser.get('Evaluation', 'reference_file')
    output_path = parser.get('Evaluation', 'output_path')
    system_id = parser.get('Evaluation', 'system_id')
    es_index = parser.get('Indexer', 'index')
    dataset_name = parser.get('Indexer', 'dataset_name')
    max_hits = int(parser.get('Evaluation', 'max_hits'))
    
    
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
    
    eval(query_file, reference_file, output_path, TREC_PATH, search_func, es_index, system_id, dataset_name, max_hits)
