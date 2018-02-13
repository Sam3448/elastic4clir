import sys
import random

f_in = open('query.txt', 'r')

f_out = open('query-domain.txt','w')

for line in f_in:
    q_num = (line.strip().split()[0])
    f_out.write(q_num)
    num_domains = random.randint(1,5)
    for tmp in range(num_domains):
        f_out.write(' ' + str(random.randint(1,5)))
    f_out.write('\n')

f_out.close()
f_in.close()

