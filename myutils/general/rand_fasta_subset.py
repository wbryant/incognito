'''
Created on 6 Nov 2014

@author: wbryant
'''

import random, sys, re

def import_fasta_file(file_name):
    f_in = open(file_name, 'r')
    fasta_tuple_list = []
    
    f_id = None
    sequence = ""
    
    for line in f_in:
        if line.startswith('>'):
            fasta_tuple_list.append((f_id, sequence))
            sequence = ""
            f_id = line.strip()
        else:
            sequence = sequence + line.strip()
    
    fasta_tuple_list.append((id, sequence))
    
    f_in.close()
    
    return fasta_tuple_list
    
def random_subset_of_list(in_list, num_returned = 50):
    subset_list = [ in_list[i] for i in sorted(random.sample(xrange(len(in_list)), num_returned)) ]
    return subset_list

def add_filename_presuffix(file_string, add_string = '_out'):
    new_filename = re.sub('(\.[^\.]+$)', add_string + '\g<1>', file_string)
    return new_filename

if __name__ == '__main__':
    try:
        in_file = sys.argv[1]
    except:
        in_file = '/Users/wbryant/work/BTH/analysis/pla_biosynthesis/pla_synthase_I_interpro.fasta'
    try:
        out_file = sys.argv[2]
    except:
        print("No output file specified, using default name ...")
        out_file = add_filename_presuffix(in_file)
        
    fasta_list = import_fasta_file(in_file)
    
#     for f_entry in fasta_list[0:10]:
#         print f_entry
    
    f_out = open(out_file, 'w')
    for fasta_entry in random_subset_of_list(fasta_list):
        f_out.write("{}\n{}\n".format(fasta_entry[0],fasta_entry[1]))
    
    f_out.close()
    
    pass