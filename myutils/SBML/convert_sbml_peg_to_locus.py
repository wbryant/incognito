'''
Created on 11 Aug 2014

@author: wbryant
'''

import re
from myutils.general.utils import preview_dict

def convert_file(peg_locus_dict, sbml_file, peg_pattern = '(peg\.[0-9]+)'):

    outfile = re.sub('\.([^\.]+)$','.locus.\g<1>',sbml_file)

    f_in = open(sbml_file, 'r')
    f_out = open(outfile, 'w')
    
    peg_rep_pattern = re.sub('\(.+\)','{}',peg_pattern)
    

    ## For each peg in gene associations replace with relevant locus_tag
    
    unconverted_pegs = []
    converted_pegs = []
    
    for line in f_in:
        
        new_line = line
        
        
        ## Convert gene associations to locus tags
        
        if 'GENE_ASSOCIATION' in line:
            
#             print("{}".format(line))
            
            pegs = re.findall(peg_pattern,line)
            pegs = list(set(pegs))
            
            for peg in pegs:
                if peg in peg_locus_dict:
                    converted_pegs.append(peg)
                    locus_tag = peg_locus_dict[peg]
                    re_sub_string = peg_rep_pattern.format(peg)
                    new_line = re.sub(re_sub_string, locus_tag, new_line)
                else:
                    unconverted_pegs.append(peg)
                    
        
        if new_line.startswith('<reaction'):
            new_line = re.sub('_.[0-9]+','',new_line)
        elif new_line.startswith('<species '):
            new_line = re.sub('(id=\"[^\"]+_.)[0-9]+','\g<1>',new_line)
            new_line = re.sub('_.[0-9]+','',new_line)
        elif 'species=' in new_line:
            new_line = re.sub('(species=\".+_.)[0-9]+','\g<1>',new_line)
        
            
        f_out.write(new_line)

    f_in.close()
    f_out.close()
    
    unconverted_pegs = list(set(unconverted_pegs))
    converted_pegs = list(set(converted_pegs))
    
    for peg in unconverted_pegs:
        print("{} unconverted ...".format(peg))
    
    print("\nThere are {} converted PEGs and {} unconverted PEGs.".format(len(converted_pegs), len(unconverted_pegs)))

def import_dict_from_iBSU1103_file(file_name = None):
    file_name = '/Users/wbryant/work/cogzymes/models/BSU_iBsu1103_genes2.csv' 
    
    f_in = open(file_name, 'r')
    f_in.readline()
    
    BSU_pattern = "Bsu[0-9]{4}"
    
    
    peg_locus_dict = {}
    
    for line in f_in:
        rows = line.strip().split("\t")
        
        peg_id = rows[0]
        synonyms = rows[1]
        
#         print("{} - {}".format(peg_id, synonyms))
        
        locus_tag = re.findall(BSU_pattern, synonyms)
        
        if len(locus_tag) == 1:
            peg_locus_dict[peg_id] = locus_tag[0].upper() + '0'
    
    f_in.close()
    
    return peg_locus_dict
                    
if __name__ == '__main__':
      
    ## BSU conversion
    peg_locus_dict = import_dict_from_iBSU1103_file()
     
    ## Convert original iBsu1103 model
    convert_file(peg_locus_dict,
        sbml_file = '/Users/wbryant/work/cogzymes/models/BSU_iBsu1103_sbrg - PEGs.xml')
   
#     ## Convert Model SEED raw BSU model
#     convert_file(peg_locus_dict, peg_pattern = '[0-9]+\.[0-9]+\.(peg\.[0-9]+)', 
#         sbml_file = '/Users/wbryant/work/cogzymes/models/Seed224308.1.xml')

    pass
    
    