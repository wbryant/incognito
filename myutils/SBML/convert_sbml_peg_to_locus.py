'''
Created on 11 Aug 2014

@author: wbryant
'''

import re, sys
from myutils.general.utils import preview_dict
from copy import deepcopy
from myutils.bio.online import get_loci_from_protein_gis
from myutils.general.utils import dict_append

def create_peg_locus_dict_from_iBSU1103_file(file_name = None):
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

def create_peg_locus_dict_from_rast(rastfile, locus_pattern, peg_pattern):
    """
    Use a downloaded RAST feature table, create a PEG to LOCUS dictionary.
    N.B. PEGs should be PEG pattern.
    """
    
    print("Creating peg to locus tag dictionary from RAST file ...")
    
    f_in = open(rastfile, 'r')
    
    peg_locus_dict = {}
    gi_peg_dict = {}
    num_pegs = 0
    
    for line in f_in:
        if 'peg' in line:
            num_pegs += 1
            split_line = line.split("\t")
            feature_id = split_line[0]
            full_gi = split_line[10]
            try:
                protein_gi = full_gi.split("|")[1]
            except:
                continue
            
            try:
                peg_id = re.search(peg_pattern, feature_id).group(1)
#                 peg_id = feature_id.split(".")[-1].strip()
            except:
                print("PEG pattern could not be found ...")
                print peg_pattern
                print feature_id
                sys.exit(1)
            
            gi_peg_dict[protein_gi] = peg_id
    
    protein_gi_list = gi_peg_dict.keys()
    
    
    ## Find the Genbank entry for each gene GI
    
    protein_gi_locus_tag_dict, _ = get_loci_from_protein_gis(protein_gi_list, locus_pattern)     
    
    for protein_gi in gi_peg_dict:
        peg_id = gi_peg_dict[protein_gi]
        try:
            locus_tag = protein_gi_locus_tag_dict[protein_gi] 
            peg_locus_dict[peg_id] = locus_tag
        except:
            continue
    
#     print("Length input = {}".format(num_pegs))
#     print("Length output = {}".format(len(peg_locus_dict)))
    
    print("... peg to locus tag from RAST file complete.")
    
    print("Rast peg_locus_dict:")
    preview_dict(peg_locus_dict)
    print("")
    
    return peg_locus_dict
    
def import_genbank_gi_locus_dictionary(genbank_file):
    """
    Create a dictionary of GI, gene locus pairs from a GenBank Nucleotide file.
    """
    print("Importing Genbank to locus tag dictionary ...")
    
    gi_locus_dict = {}
    
    f_in = open(genbank_file, 'r')
    
    locus_tag = ''
    gi = ''
    
    for line in f_in:
        if '/locus_tag' in line:
            ## Retrieve gene locus
            
            locus_re = re.search("locus_tag=\"([^\"]+)\"",line)
            
            locus_tag = locus_re.group(1)
        
        elif '/db_xref="GI:' in line:
            ## Retrieve GI and add to dictionary
            
            gi_re = re.search("db_xref=\"GI:([^\"]+)\"",line)
            
            gi = gi_re.group(1)
            
            gi_locus_dict[gi] = locus_tag
    
#     print(" - Dictionary imported, {} entries:\n".format(len(gi_locus_dict)))
#     preview_dict(gi_locus_dict)
#     print("")
    
    print("... Genbank to locus tag dictionary imported.")
    
    return gi_locus_dict
        
def import_peg_gi_dictionary(gene_text_file, taxonomy_id, peg_prefix = 'Seed'):
    """
    Import peg to gi dictionary from gene file (limited by species ID)
    """

    print("Importing PEG to Genbank dictionary ...")
     
    gene_f_in = open(gene_text_file, 'r')
    
    peg_gi_dict = {}
    
    seed_taxonomy_string = peg_prefix + str(taxonomy_id)
    
    for gene_line in gene_f_in:
        if seed_taxonomy_string in gene_line:
            gi_number, full_peg_id = gene_line.split("\t")
            peg_id = full_peg_id.split(".")[-1].strip()
            
            peg_gi_dict[peg_id] = gi_number
    
    gene_f_in.close()
    
#     ## Give summary of results
#     print(" - Dictionary imported, {} entries:\n".format(len(peg_gi_dict)))
#     preview_dict(peg_gi_dict)
#     print("")
    
    
    ## Calculate missing PEGs
    peg_list = [int(key) for key in peg_gi_dict]
    peg_list_sorted = sorted(peg_list)
    peg_lower = peg_list_sorted[0]
    missing_pegs = []
    print("Missing PEGs:")
    for peg_higher in peg_list_sorted[1:]:
        if peg_higher-peg_lower > 1:
            for missing_peg in range(peg_lower+1,peg_higher):
                missing_pegs.append(missing_peg)
                print(" - {}".format(missing_peg))
        peg_lower = deepcopy(peg_higher)
            
    
    return peg_gi_dict, missing_pegs

def merge_dicts(a_b, b_c):
    """
    Create a dictionary between a and c, linked by b in two dictionaries
    """
    
    a_c_dict = {}
    a_b_unfound_dict = {}
    
    for a in a_b:
        b = a_b[a]
        if b in b_c:
            c = b_c[b]
            a_c_dict[a] = c
        else:
            a_b_unfound_dict[a] = b
    
#     print(" - Dictionaries merged, {} entries:\n".format(len(a_c_dict)))
#     preview_dict(a_c_dict)
#     print("")
    
    return a_c_dict, a_b_unfound_dict

def interpolate_gene_loci(peg_locus_dict_in):
    """
    Add missing peg > locus pairs from calculated dictionary. 
    """
    
    peg_locus_dict = deepcopy(peg_locus_dict_in)
    
    peg_locus_list = []
    for peg in peg_locus_dict:
        peg_number = int(re.search('([0-9]+)$',peg).group(1))
        peg_locus_list.append((peg_number,peg_locus_dict[peg]))
    
    peg_locus_sorted = sorted(peg_locus_list, key = lambda x: x[0])
    
    lower_pl = peg_locus_sorted[0]
    
    for upper_pl in peg_locus_sorted[1:]:
        lower_p = lower_pl[0]
        lower_l = lower_pl[1]
        upper_p = upper_pl[0]
        upper_l = upper_pl[1]
        
        peg_diff = upper_p-lower_p
        
        lower_l_num = int(re.findall('[0-9]+$',lower_l)[0])
        upper_l_num = int(re.findall('[0-9]+$',upper_l)[0])
        
        locus_diff = upper_l_num - lower_l_num
        
        if (locus_diff == peg_diff) and (locus_diff > 1):
            ## PEG/locus values can be interpolated
            
#             print("{} - {}".format(lower_p,lower_l))
#             print("{} - {}".format(upper_p,upper_l))
            
            new_l_num = lower_l_num
            
            for new_peg in range(lower_p+1,upper_p):
                new_l_num += 1
                
                new_l = re.sub('[0-9]+$',"{:04d}".format(new_l_num),lower_l)
                
#                 print(" - {} - {}".format(new_peg,new_l))
                
                peg_locus_dict[str(new_peg)] = new_l
    
        lower_pl = deepcopy(upper_pl)        
    
#     print("{} relations added to dictionary.".format(len(peg_locus_dict)-num_old))
    
    return peg_locus_dict 

def create_peg_locus_dict_from_tools(taxonomy_id, peg_prefix, species_genbank_file, locus_pattern, peg_pattern, rastfile = None, interpolate = True):
    """
    Create a dictionary for translating PEG IDs for an organism into locus tags.
    """
    
    ## Import peg to gi dictionary from gene file (limited by species ID)
    
    gene_text_file = '/Users/wbryant/git/incognito/static/tables/MODELS_genes.txt' 
    peg_gi_dict, _ = import_peg_gi_dictionary(gene_text_file, taxonomy_id, peg_prefix)
     
     
    ## Convert gene GIs to gene locus tags.
             
    gi_locus_dict = import_genbank_gi_locus_dictionary(species_genbank_file)
                 
    ## Create crossover dictionary (peg to locus)
     
    peg_locus_dict, peg_gi_unfound = merge_dicts(peg_gi_dict, gi_locus_dict)
    print(" - {} relations found using gene GIs".format(len(peg_locus_dict)))
     
     
#     ## For unidentified PEGs try Entrez lookup
#      
#     gi_list = peg_gi_unfound.values()
#     protein_gi_locus_tag_dict, _ = get_loci_from_protein_gis(gi_list, locus_pattern)
#     peg_locus_dict_entrez, _ = merge_dicts(peg_gi_dict, protein_gi_locus_tag_dict)
#     print("{} relations found using protein GIs ...".format(len(peg_locus_dict_entrez)))
#      
#     peg_locus_dict.update(peg_locus_dict_entrez)
#     print("{} relations found with all GIs ...".format(len(peg_locus_dict)))
     
    if interpolate:
        ## Interpolate missing relations
         
        peg_locus_dict = interpolate_gene_loci(peg_locus_dict)
        print("{} relations including interpolations ...".format(len(peg_locus_dict)))
    
    
    if rastfile:
        ## Use RAST file to create PEG to locus tag dictionary
            
        peg_locus_dict_rast = create_peg_locus_dict_from_rast(rastfile, locus_pattern, peg_pattern)
        print("{} relations from RAST ...".format(len(peg_locus_dict_rast)))
           
        
        ## Combine RAST data with other data
        
        peg_locus_dict.update(peg_locus_dict_rast)
        
        if interpolate:
            peg_locus_dict = interpolate_gene_loci(peg_locus_dict)
    
    if interpolate:
        print("{} relations including interpolations ...".format(len(peg_locus_dict)))
    else:
        print("{} relations (without interpolations) ...".format(len(peg_locus_dict)))
    
    return peg_locus_dict

def convert_file(peg_locus_dict, sbml_file, peg_pattern = '(peg\.[0-9]+)'):
    
    print("Converting file ...")
    
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
    
    print("... complete.")
    
    unconverted_pegs = list(set(unconverted_pegs))
    converted_pegs = list(set(converted_pegs))
    
    for peg in unconverted_pegs:
        print("{} unconverted ...".format(peg))
    
    print("\nThere are {} converted PEGs and {} unconverted PEGs.".format(len(converted_pegs), len(unconverted_pegs)))
    
    print("Result outputted to '{}'.".format(outfile))

def get_positional_inference(rast_file, genbank_file, peg_pattern, peg_locus_dict_validate = None):
    """
    From positional data infer peg > locus tag relationship and test against current known.
    """
    
    print("Getting positional PEG > locus_tag inferences ...")
    
    peg_locus_dict = {}
    
    f_in = open(rast_file, 'r')
    
    peg_position = {}
    rast_positions = []
    
    for line in f_in:
        if 'peg' in line:
            split_line = line.split("\t")
            
            feature_id = split_line[0]
            try:
                peg_id = re.search(peg_pattern, feature_id).group(1)
            except:
                print("PEG pattern could not be found ...")
                print peg_pattern
                print feature_id
                sys.exit(1)
            
            position_mean = int((int(split_line[4]) + int(split_line[3]))/2.0)
            
            rast_positions.append(position_mean)
            peg_position[position_mean] = peg_id   
#             print("{} - {}".format(peg_id, position_mean))
    
    f_in = open(genbank_file, 'r')
    
    locus_position = {}
    genbank_positions = []
    
    for line in f_in:
        
        if line.startswith('     gene'):
            
            positions = re.findall('[0-9]+',line)
            position_mean = int((int(positions[1]) + int(positions[0]))/2.0)
            
        elif '/locus_tag' in line:
            ## Retrieve gene locus
            
            locus_re = re.search("locus_tag=\"([^\"]+)\"",line)
            locus_tag = locus_re.group(1)
            
            locus_position[position_mean] = locus_tag
#             print("{} - {}".format(locus_tag, position_mean))
            genbank_positions.append(position_mean)
            
    rast_genbank_position_dict = {}
    
    for rast_position in rast_positions:
        closest_genbank = min(genbank_positions, key=lambda x:abs(x-rast_position))
        
        dict_append(rast_genbank_position_dict, rast_position, closest_genbank)
    
    for rast_position in rast_genbank_position_dict:
        if len(rast_genbank_position_dict[rast_position]) == 1:
            peg = peg_position[rast_position]
            locus_tag = locus_position[rast_genbank_position_dict[rast_position][0]]
            peg_locus_dict[peg] = locus_tag
    
    if peg_locus_dict_validate:
        ## Validation
        
        num_correct = 0
        num_incorrect = 0
        
        for peg in peg_locus_dict_validate:
            if peg in peg_locus_dict:
                if peg_locus_dict_validate[peg] == peg_locus_dict[peg]:
                    num_correct += 1
                else:
                    num_incorrect += 1
        
        print(" - Number correct from positional inference = {}".format(num_correct))
        print(" - Number incorrect from positional inference = {}".format(num_incorrect))
    
    print("... complete.")
    
    return peg_locus_dict
    
                    
if __name__ == '__main__':
      
#     ### BSU conversion
#     peg_locus_dict = import_dict_from_iBSU1103_file()
#      
#     ## Convert original iBsu1103 model
#     convert_file(peg_locus_dict,
#         sbml_file = '/Users/wbryant/work/cogzymes/models/BSU_iBsu1103_sbrg - PEGs.xml')
#    
#     ## Convert Model SEED raw BSU model
#     convert_file(peg_locus_dict, peg_pattern = '[0-9]+\.[0-9]+\.(peg\.[0-9]+)', 
#         sbml_file = '/Users/wbryant/work/cogzymes/models/Seed224308.1.xml')
    
    ### MTU conversion
    taxonomy_id = '83332'
    peg_prefix = 'Opt'
    genbank_file = '/Users/wbryant/work/cogzymes/data/genbank/MTU_83332.gb'
    locus_pattern = 'Rv[0-9]+c?'
    rast_file = '/Users/wbryant/work/cogzymes/data/SEED/rast_mtu_83332.1_pegs.tsv'
    peg_pattern = '[0-9]+\.[0-9]+\.(peg\.[0-9]+)'
#     peg_locus_dict = create_peg_locus_dict_from_tools(
#         taxonomy_id, 
#         peg_prefix, 
#         genbank_file, 
#         locus_pattern,
#         peg_pattern,
#         rastfile = rast_file,
#         interpolate=False)
    
    peg_locus_dict = get_positional_inference(rast_file, genbank_file, peg_pattern)
    
#     ## Remove c from end of all gene loci so that interpolation can be done
#     for peg in peg_locus_dict:
#         locus = peg_locus_dict[peg]
#         if locus[-1] == 'c':
#             locus = locus[:-1]
#             peg_locus_dict[peg] = locus
#     peg_locus_dict = interpolate_gene_loci(peg_locus_dict)
#     print("{} relations including interpolations ...".format(len(peg_locus_dict)))
    
    
    convert_file(peg_locus_dict, peg_pattern = '[0-9]+\.[0-9]+\.(peg\.[0-9]+)', 
        sbml_file = '/Users/wbryant/work/cogzymes/models/MTU_seed_original.xml')    
    
    
    pass
    
    