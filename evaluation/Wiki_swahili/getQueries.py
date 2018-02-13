import sys
import os

if __name__ == '__main__':
    USAGE = 'python getQueries.py <rel-file> <big-query-file>'
    if len(sys.argv) != 3:
        print (USAGE)
        sys.exit()

    res_file = sys.argv[1]
    big_query_file = sys.argv[2]

    if not ( os.path.isfile(res_file) and os.path.isfile(big_query_file) ):
        print ("Invalid input files given")
        print (USAGE)
        sys.exit()

   #The queries used in the relevance output. Only extract them from the query file 
    rel_queries = set()
    
    with open(res_file, 'r') as f_res:
        for idx, cur_line in enumerate(f_res):
            toks = cur_line.strip().split()
            if len(toks) != 3:
                print ("Invalid formatting of rel-file at line ", idx+1)
                sys.exit()
            rel_queries.add(int(toks[0]))

    print(rel_queries)
    
    #File to store filtered queries
    f_out = open('query.txt', 'w')

    #Now extract the queries from the big_query_file
    with open(big_query_file, 'r') as f_q:
        for idx,cur_line in enumerate(f_q):
            toks = cur_line.strip().split(maxsplit=1)
            if len(toks) != 2:
                print ("Invalid formatting of query_file at line ",idx+1)
            
            query_num = int(toks[0])
            if query_num in rel_queries:
                f_out.write(cur_line)

    f_out.close()
