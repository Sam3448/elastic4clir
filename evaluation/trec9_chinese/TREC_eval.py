import matplotlib
matplotlib.use('Agg')
import sys
import os
import re
import subprocess
import collections
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup

#include path to index and search code
sys.path.append('/home/sachith/CLIR/DUH/elastic4clir/index_collection/trec9_chinese')
from TREC_search import search


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

def prec_recall_graph(FIN_OUT):
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
        plt.savefig('P_r_graph_TREC.png')


def eval(query_file, ref_out_file, SEARCH_OUT, TREC_PATH):
    f_out = open(SEARCH_OUT,'w');
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
    
    #Run trec-eval
    TREC_EXEC = os.path.join(TREC_PATH,'trec_eval')
    if not os.path.isfile(TREC_EXEC):
        print ("\nFailed to find ",TREC_EXEC)
        sys.exit
    
    #File to store final output
    FIN_OUT = "results_TREC.txt"
    fin_out = open(FIN_OUT, 'w')
    print (subprocess.list2cmdline([TREC_EXEC, ref_out_file, SEARCH_OUT]))
    subprocess.call([TREC_EXEC, ref_out_file, SEARCH_OUT], stdout = fin_out)
    fin_out.close()
    prec_recall_graph(FIN_OUT)
    return FIN_OUT
    

if __name__ == '__main__':
    USAGE = '\nUSAGE : python TREC_eval.py <query_file> <ref_output> \n'
    
    #Path to TREC_Eval C-code
    TREC_PATH = '/home/sachith/CLIR/DUH/elastic4clir/evaluation/trec_eval.9.0'
    
    #File to store search output
    SEARCH_OUT = "search_output_TREC.txt"
    

        
    if len(sys.argv) != 3:
        print (USAGE)
        sys.exit()
    
    eval(sys.argv[1], sys.argv[2], SEARCH_OUT, TREC_PATH)
