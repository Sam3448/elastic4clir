#Requisites
Needs python > 3 and gcc (to run TREC evaluation scripts)
The query list and reference output must follow TREC eval format (http://trec.nist.gov/trec_eval/ )

#Running the evaluation Script
`python TREC_eval.py <query_list_file> <reference_output>`
The output stats are in results.txt, the Precision Recall graph is also generated.
