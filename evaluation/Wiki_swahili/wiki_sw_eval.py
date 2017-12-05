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


def eval(query_file, ref_out_file, output_path, TREC_PATH, search):
    #File to store search output
    SEARCH_OUT = os.path.join(output_path, "search_output_wiki_swahili.txt")
    f_out = open(SEARCH_OUT,'w');
    queries = get_queries(query_file)

    if queries is None or len(queries) == 0:
        print ("\nInvalid or Bad Query File. Exiting Evaluation module\n")
        sys.exit
    for q_num in queries:
        q_string =  queries[q_num]
        res = search(q_string)
        for each_doc in res['hits']['hits']:
            f_out.write(str(q_num) + " " + "1" + " " + each_doc['_id'] + " " + "-1" + " " + str(each_doc['_score']) + " " + "STANDARD" + "\n")
    f_out.close()
    
    #Compile (make) the trec-eval code
    my_cwd = os.getcwd()
    os.chdir(TREC_PATH)
    subprocess.call(['make'])
    os.chdir(my_cwd)
    
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
            parser.has_option('Evaluation', 'reference_file')):
        print ("Invalid/Incomplete Evaluation parameters in config file")
        sys.exit()

    search_script = parser.get('Evaluation', 'search_script')
    TREC_PATH = parser.get('Evaluation', 'trec_eval_path')
    query_file = parser.get('Evaluation', 'query_file')
    reference_file = parser.get('Evaluation', 'reference_file')
    output_path = parser.get('Evaluation', 'output_path')
    
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
    
    eval(query_file, reference_file, output_path, TREC_PATH, search_func)
