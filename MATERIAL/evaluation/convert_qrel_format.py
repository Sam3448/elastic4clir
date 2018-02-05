#!/usr/bin/env python

query_annotation="/home/pkoehn/statmt/data/material/IARPA_MATERIAL_BASE-1A/ANALYSIS_ANNOTATION1/query_annotation.tsv"
qrel_output="1A.qrel"

with open(query_annotation) as fid, open(qrel_output,"w") as out:
    fid.readline()
    for line in fid:
        query_id, doc_id = line.split()
        out.write("%s 0 %s 1\n" %(query_id, doc_id))
        
