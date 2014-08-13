'''
Created on 3 Jul 2014

@author: wbryant

Take MTG gene file and SBML file, and convert pegs to gene loci

'''

import re, sys
from copy import deepcopy
from myutils.bio.online import get_loci_from_protein_gis
from myutils.general.utils import preview_dict

def create_peg_locus_dict_from_rast(rastfile, locus_pattern):
    """
    Use a downloaded RAST feature table, create a PEG to LOCUS dictionary.
    N.B. PEGs should be just number in string form.
    """
    
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
            
            protein_gi = full_gi.split("|")[1]
            
            peg_id = feature_id.split(".")[-1].strip()
            
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
    
    print("Length input = {}".format(num_pegs))
    print("Length output = {}".format(len(peg_locus_dict)))
    
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
    
    print("Merging dictionaries ...")
    
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
    
    num_old = len(peg_locus_dict)
    
    peg_locus_list = []
    for peg in peg_locus_dict:
        peg_locus_list.append((int(peg),peg_locus_dict[peg]))
    
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
            
if __name__ == '__main__':
    
    ## Get species ID
    
    
    
    ## M. smegmatis model
#     peg_prefix = 'Seed'    
#     sbml_file = '/Users/wbryant/work/cogzymes/models/Seed246196.1.25442.xml'
#     sbml_file = '/Users/wbryant/work/cogzymes/models/Seed246196.19.25442.xml'
#     species_genbank_file = '/Users/wbryant/work/cogzymes/data/genbank/MSM_246196.gb'
    
    ## BTH model
#     peg_prefix = 'Seed'    
#     sbml_file = '/Users/wbryant/work/cogzymes/models/Seed246196.19.25442.xml'
#     species_genbank_file = '/Users/wbryant/work/cogzymes/data/genbank/MSM_246196.gb'

    ## BSU model
    peg_prefix = 'Opt'    
    sbml_file = '/Users/wbryant/work/cogzymes/models/Seed224308.1.xml'
    species_genbank_file = '/Users/wbryant/work/cogzymes/data/genbank/BSU_224308.gb'
    locus_pattern = "BSU[0-9]+"

    
    gene_text_file = '/Users/wbryant/work/mindthegap/MIND_THE_GAP/Template/static/Tables/MODELS_genes.txt'
    
    outfile = re.sub('\.([^\.]+)$','.locus.\g<1>',sbml_file)
    
    print("Output file: '{}'\n".format(outfile))
    
    f_in = open(sbml_file, 'r')
    f_out = open(outfile, 'w')
    
    for line in f_in:
        
        f_out.write(line)
        
        if 'model id' in line:
            ## This is the model ID line, so get species ID from it
            
            id_groups = re.search("model id=\"[^\"]+ ([0-9]+)\"",line)
            try:
                taxonomy_id = id_groups.group(1)
            except:
                print("Taxonomy ID could not be determined, please check that it is at the end of the model ID.")
                f_in.close()
                f_out.close()
                sys.exit(1)
            
            break
            
    
    ## Import peg to gi dictionary from gene file (limited by species ID)
     
    peg_gi_dict, _ = import_peg_gi_dictionary(gene_text_file, taxonomy_id, peg_prefix)
     
     
    ## Convert gene GIs to gene locus tags.
             
    gi_locus_dict = import_genbank_gi_locus_dictionary(species_genbank_file)
             
     
    ## Create crossover dictionary (peg to locus)
     
    peg_locus_dict, peg_gi_unfound = merge_dicts(peg_gi_dict, gi_locus_dict)
    print("{} relations found using gene GIs ...".format(len(peg_locus_dict)))
     
     
    ## For unidentified PEGs try Entrez lookup
     
    gi_list = peg_gi_unfound.values()
    protein_gi_locus_tag_dict, _ = get_loci_from_protein_gis(gi_list, locus_pattern)
    peg_locus_dict_entrez, _ = merge_dicts(peg_gi_dict, protein_gi_locus_tag_dict)
    print("{} relations found using protein GIs ...".format(len(peg_locus_dict_entrez)))
     
     
    ## Combine dictionaries
     
    peg_locus_dict.update(peg_locus_dict_entrez)
    print("{} relations found with all GIs ...".format(len(peg_locus_dict)))
     
     
    ## Interpolate missing relations
     
    peg_locus_dict = interpolate_gene_loci(peg_locus_dict)
    print("{} relations including interpolations ...".format(len(peg_locus_dict)))
    
    
    ## Use RAST file to create PEG to locus tag dictionary
    
    rastfile = "/Users/wbryant/work/cogzymes/data/SEED/rast_bsu_224308.1_pegs.tsv"
    
    peg_locus_dict_rast = create_peg_locus_dict_from_rast(rastfile, locus_pattern)
    print("{} relations from RAST ...".format(len(peg_locus_dict_rast)))
    
    
    
    ## Combine RAST data with other data
    
    peg_locus_dict.update(peg_locus_dict_rast)
    peg_locus_dict = interpolate_gene_loci(peg_locus_dict)
    print("{} relations including interpolations ...".format(len(peg_locus_dict)))
    
    
    ## For each peg in gene associations replace with relevant locus_tag
    
    unconverted_pegs = []
    converted_pegs = []
    gi_found_pegs = []
    
    for line in f_in:
        
        new_line = line
        
        
        ## Convert gene associations to locus tags
        
        if 'GENE_ASSOCIATION' in line:
            
            pegs = re.findall('[0-9]+\.[0-9]+\.peg\.([0-9]+)',line)
            pegs = list(set(pegs))
            
            for peg in pegs:
                if peg in peg_locus_dict:
                    converted_pegs.append(peg)
                    locus_tag = peg_locus_dict[peg]
                    re_sub_string = '[0-9]+\.[0-9]+\.peg\.{}'.format(peg)
                    new_line = re.sub(re_sub_string, locus_tag, new_line)
                else:
                    unconverted_pegs.append(peg)
                    if peg in peg_gi_dict:
                        gi_found_pegs.append(peg)
        
        
        ## Remove '_.[0-9]+' from all names and IDs, except met IDs, remove '0' from those. 
        
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
    gi_found_pegs = list(set(gi_found_pegs))
    
    print("There are {} converted PEGs and {} unconverted PEGs.".format(len(converted_pegs), len(unconverted_pegs)))
    print("Of the unconverted PEGs, {} had GI numbers found, but no related entry in nucleotide file.\n".format(len(gi_found_pegs)))
    print("\n".join(gi_found_pegs))
#     for peg in unconverted_pegs:
#         print(" - {}".format(peg))
    




