import matplotlib
matplotlib.use('Agg')
import sys
import os
import re
import subprocess
import collections
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import importlib
from configparser import SafeConfigParser
from collections import OrderedDict
from elasticsearch import Elasticsearch


#Implements the AQWV metric
def AQWV(ref_file, out_file, es_index):
    
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
    
    #Compute AQWV scores for each query 
    # IMP : For queries not present in both search_out and ref_out, AQWV is not computed
    scores = {}
    total_score = 0.0
    total_count = 0
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

            #print (qry, N_miss, N_FA, N_relevant, P_miss, P_FA, scores[qry])
    print ("FINAL AQWV is ", total_score/total_count)



#Given a query file, it maps the query number to the query
def get_queries(query_file):
    if not os.path.isfile(query_file) or os.stat(query_file).st_size == 0:
        return None
    
    query_dict = collections.OrderedDict()


    #Query pattern is currently CH55 for #55

    p = re.compile('CH(\d+)')
    with open(query_file, 'r') as f_query:
        soup = BeautifulSoup(f_query, "lxml")
        count = 0
        try:
            for doc in soup.find_all('top'):
                #Consider only if num, title and desc are present , narr is taken optional
                if doc.find('num') and doc.find('title') and doc.find('desc'):
                    m = p.search(doc.find('num').text.strip())
                    if m is None:
                        continue
                    num = int(m.group()[2:])
                    title = doc.find('title').text.strip()
                    desc = doc.find('desc').text.strip()
                    narr = ""
                    if doc.find('narr'):
                        narr = doc.find('narr').text.strip()
                    count +=1
                    query_dict[num] = {}
                    query_dict[num]['title'] = title
                    query_dict[num]['desc'] = desc
                    query_dict[num]['narr'] = narr
                    #print ("Added query",num)
        except Exception as e:
            print ("Parsing error in query file %s: %s" % (query_file, str(e)))
            return None
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
        plt.savefig(os.path.join(output_path,'P_r_graph_TREC.png'))


def eval(query_file, ref_out_file, output_path, TREC_PATH, search, es_index):
    SEARCH_OUT = os.path.join(output_path, "search_output_trec.txt")
    f_out = open(SEARCH_OUT,'w')
    queries = get_queries(query_file)
    if queries is None or len(queries) == 0:
        print ("\nInvalid or Bad Query File. Exiting Evaluation module\n")
        sys.exit
    for q_num in queries:
        q_string =  queries[q_num]['title']
        res = search(q_string)
        for each_doc in res['hits']['hits']:
            f_out.write(str(q_num) + " " + "1" + " " + each_doc['_id'] + " " + "-1" + " " + str(each_doc['_score']) + " " + "STANDARD" + "\n")
    f_out.close()
    
    #Compile (make) the trec-eval code
    my_cwd = os.getcwd()
    os.chdir(TREC_PATH)
    subprocess.call(['make'])
    os.chdir(my_cwd)
    
    AQWV(ref_out_file, SEARCH_OUT, es_index)
    #Run trec-eval
    TREC_EXEC = os.path.join(TREC_PATH,'trec_eval')
    if not os.path.isfile(TREC_EXEC):
        print ("\nFailed to find ",TREC_EXEC)
        sys.exit
    
    #File to store final output
    FIN_OUT = os.path.join(output_path, "results_trec.txt")
    fin_out = open(FIN_OUT, 'w')
    print (subprocess.list2cmdline([TREC_EXEC, ref_out_file, SEARCH_OUT]))
    subprocess.call([TREC_EXEC, ref_out_file, SEARCH_OUT], stdout = fin_out)
    fin_out.close()
    prec_recall_graph(output_path, FIN_OUT)
    return FIN_OUT
    

if __name__ == '__main__':
    USAGE = '\n USAGE : python TREC_eval.py <config_file> \n'
    
    if len(sys.argv) != 2:
        print (USAGE)
        sys.exit()
    
    parser = SafeConfigParser({'output_path' : os.getcwd()})
    parser.read(sys.argv[1])
    
    if not (parser.has_option('Evaluation', 'search_script') or 
            parser.has_option('Evaluation', 'trec_eval_path') or
            parser.has_option('Evaluation', 'query_file') or
            parser.has_option('Evaluation', 'reference_file') or
            parser.has_option('Evaluation', 'index_name')):
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
    if search_file == '':
        print ("Invalid search_script provided in Evaluation config")
        sys.exit()
    else:
        mod = importlib.import_module(search_file.replace('.py', ''))
        search_func = getattr(mod, 'search')   
    
    eval(query_file, reference_file, output_path, TREC_PATH, search_func, es_index)