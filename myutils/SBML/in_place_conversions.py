'''
Created on 2 Apr 2014

@author: wbryant


'''

import re
from bioservices import UniProt
from myutils.SBML.import_SBML import import_SBML_to_bipartite

xml_from = '/Users/wbryant/work/BTH/data/iAH991/BTH_with_gprs.xml'
xml_to = '/Users/wbryant/work/BTH/analysis/working_models/BT_JB_v2_harmonized_genes_out.xml'

def transfer_gprs(xml_from=xml_from, xml_to=xml_to, node_id = 'SOURCE'):
    """
    Add GPRs in XML_to with ones in xml_from.
    IDs in node_id in xml_to used for recognition.
    """
    
    G_from = import_SBML_to_bipartite(xml_from)
    id_gpr_dict = {}
    for idx in G_from.nodes():
        node = G_from.node[idx]
        if node['type'] == 'reaction':
            id_gpr_dict[node['id']] = node['gpr']
    
    
    xml_to_in = open(xml_to, 'r')
    xml_out = re.sub('\.xml','_out.xml',xml_to)
    xml_out = open(xml_out, 'w')
    
    rep_flag = False
    
    for line in xml_to_in:
        if 'SOURCE' in line:
            
            xml_out.write(line)
            
            source = re.search('SOURCE\:[ ]*(?P<id>[a-zA-Z0-9_]+)',line)
            source_id = source.group('id')
            
            if source_id in id_gpr_dict:
                rep_flag = True
                gpr = id_gpr_dict[source_id]
                
                ## Construct GPR line and add beneath source
                gpr_line = "          <html:p>GENE ASSOCIATION: %s</html:p>\n" % gpr
                xml_out.write(gpr_line)
            else:
                rep_flag = False
        elif (rep_flag == True) and ("GENE ASSOCIATION" in line):
            pass
        else:
            xml_out.write(line)
            
            
    
    

def model_metacyc_gene_2_biocyc(id_in):
    """
    Convert from XML MetaCyc ID to BioCyc ID for searching
    """
    
    id_groups = re.search('MetaCyc_([^\)]+)_i',id_in)
    try:
        id_new = id_groups.group(1)
    except:
        id_new = ''
    id_lookup = ''
    for letter in id_new:
        if letter == '_':
            id_lookup += '-'
        else:
            id_lookup += letter
    
    return id_lookup

model_metacyc_identifier = '\(gene\:MetaCyc_[^\)]+_i\)'

def convert_gene_ids_general(xml_file_in, id_identity = None, id_formatter = None, translate_file = None):
    """
    Replace all found instances of old gene IDs to new IDs.
    N.B. It will only look at 'GENE ASSOCIATION' lines.
    'translate_file' should be 2 column tsv file.
    """
    

    
    ## Create ID conversion dictionary
    
    translate_file = translate_file or '/Users/wbryant/Dropbox/Bacteroides/BioCyc_-_Protein-Gene-relations/BioCyc_BT_-_Protein-Gene-relations.txt' 
    trans_in = open(translate_file,'r')
    id_dict = {}
    for line in trans_in:
        ids = line.split("\t")
        if len(ids[1]) > 0:
            id_dict[ids[0]] = ids[1].strip()
    
    
    id_identity = id_identity or model_metacyc_identifier
    id_formatter = id_formatter or model_metacyc_gene_2_biocyc
    
    #print id_identity
    
    ### Run through lines of input file replacing relevant gene IDs with new gene IDs
    
    xml_file_out = re.sub('\.xml','_out.xml',xml_file_in)
    f_in = open(xml_file_in,'r')
    f_out = open(xml_file_out,'w') 
    for line in f_in:
        if 'GENE ASSOCIATION' in line:
            ## Look for genes fitting id_identity, convert and replace
            
            #print line
            
            old_ids = re.findall(id_identity, line)
            
            if len(old_ids) > 0:
                #print old_ids.groups(1)
                for old_id in old_ids:
                    old_id_formatted = id_formatter(old_id)
                    try:
                        new_id = id_dict[old_id_formatted]
                    except:
                        new_id = old_id_formatted
                        print("ID '%s' not found ..." % new_id)
                    #print("%20s: %20s" % (old_id, new_id))
                    line = line.replace(old_id,new_id,1)
            
            
            
            
            
            
            
            f_out.write(line)
            
        else:
            f_out.write(line)
    
    f_out.close()
    

def convert_gene_ids_bt(xml_file_in, id_identity = None, id_formatter = None, translate_file = None):
    """
    Replace all found instances of old gene IDs to new IDs.
    N.B. It will only look at 'GENE ASSOCIATION' lines.
    'translate_file' should be 2 column tsv file.
    """    
        
    ## Create ID conversion dictionary for MetaCyc 
    
    translate_file = translate_file or '/Users/wbryant/Dropbox/Bacteroides/BioCyc_-_Protein-Gene-relations/BioCyc_BT_-_Protein-Gene-relations.txt' 
    trans_in = open(translate_file,'r')
    id_dict = {}
    for line in trans_in:
        ids = line.split("\t")
        if len(ids[1]) > 0:
            id_dict[ids[0]] = ids[1].strip()
    
    
    id_identity = id_identity or model_metacyc_identifier
    id_formatter = id_formatter or model_metacyc_gene_2_biocyc
    
    
    ## Create gene -> locus dictionary from NCBI file
    
    ncbi_gene_file = '/Users/wbryant/work/BTH/data/NCBI/gene_list.dat'
    ncbi_in = open(ncbi_gene_file,'r')
    ncbi_id_dict = {}
    for line in ncbi_in:
        if re.search('[0-9]+\.[ ].+',line):
            ncbi_id = line.strip().split(" ")[-1]
        elif 'Other Aliases' in line:
            bt_ids = re.findall('BT\_[0-9]+',line)
            for bt_id in bt_ids:
                ncbi_id_dict[ncbi_id] = bt_id
    ncbi_in.close()
    
    
    ## Some specific UniProt IDs do not map - so put them here manually:
    
    uniprot_manual_dict = {}
    
    uniprot_manual_dict['Q8A1G3_BACTN'] = 'BT_3698'
    uniprot_manual_dict['G8JZS4_BACTN'] = 'BT_3703'
    uniprot_manual_dict['Q8A1G0_BACTN'] = 'BT_3704'
    uniprot_manual_dict['Q89YR9_BACTN'] = 'BT_4662'
    

    ### Run through lines of input file replacing relevant gene IDs with new gene IDs
    
    u = UniProt(verbose=False)
    xml_file_out = re.sub('\.xml','_out.xml',xml_file_in)
    f_in = open(xml_file_in,'r')
    f_out = open(xml_file_out,'w') 
    for line in f_in:
        if 'GENE ASSOCIATION' in line:
            ## Look for genes fitting id_identity, convert and replace
            
            #print line
            
            ###! Change!
            line = re.sub('(\<[^\>]+\>[ \n]*$)',' \g<1>',line)
            
            old_ids = re.findall(id_identity, line)
            
            if len(old_ids) > 0:
                #print old_ids.groups(1)
                for old_id in old_ids:
                    old_id_formatted = id_formatter(old_id)
                    try:
                        new_id = id_dict[old_id_formatted]
                    except:
                        new_id = old_id_formatted
                        print("ID '%s' not found ..." % new_id)
                    #print("%20s: %20s" % (old_id, new_id))
                    line = line.replace(old_id,new_id,1)
            
            ## Remove extraneous gene surrounds
            line = re.sub('\(gene\:([^\)]+)_i\)','\g<1>',line)
            
            
            ## Look for UniProt genes and convert
            if 'uniprot' in line:
                
                uniprot_entries = re.findall('\(uniprot\:[^\)]+\)',line)
                
                for uniprot_entry in uniprot_entries:
                    ## Map IDs 
                    
                    uniprot_id = re.sub('\(uniprot\:([^\)]+)\)','\g<1>',uniprot_entry)
                    
                    try:
                        new_entry = u.mapping(fr='ACC',to='KEGG_ID',query=uniprot_id)[uniprot_id][0]
                    except:
                        print("Protein ID '%s' not found in mapping, trying local ..." % uniprot_id)
                        try:
                            new_entry = uniprot_manual_dict[uniprot_id]
                        except:
                            print("Protein ID '%s' not found in local ..." % uniprot_id)
                            new_entry = uniprot_id
                    
                    
                    new_id = re.sub('bth\:([^\)]+)','\g<1>',new_entry)
                    line = line.replace(uniprot_entry,new_id,1)
                    
                    #u.mapping(fr='BIOCYC_ID',to='KEGG_ID',query='GJXV-2505')
            
            
        
            
            ## Get gene string
            line_groups = re.search('(.+GENE ASSOCIATION\:[ ]*)(.+)([ ]*\<.+)',line)
            gene_string = line_groups.group(2)
            
            
            if '_BACTN' in gene_string:
                print gene_string
            
            ## Look for NCBI IDs (like susG) and replace with BT IDs
            potential_ncbis = re.findall('[a-zA-Z0-9\_]+',gene_string)
            if '_BACTN' in gene_string:
                print ", ".join(potential_ncbis)
            for potential_ncbi in potential_ncbis:
                if potential_ncbi in ncbi_id_dict:
                    new_id = ncbi_id_dict[potential_ncbi]
                    gene_string = gene_string.replace(potential_ncbi,new_id,1)
                elif potential_ncbi in uniprot_manual_dict:
                    new_id = uniprot_manual_dict[potential_ncbi]
                    gene_string = gene_string.replace(potential_ncbi,new_id,1)
            
            
            ##Remove duplicates
            gene_list = gene_string.split(" or ")
            gene_list = list(set(gene_list))
            
            
            ## Reconstitute line
            line = line_groups.group(1)
            line += " or ".join(gene_list)
            line += line_groups.group(3)
            
            f_out.write(line)
            
        else:
            f_out.write(line)
    
    f_out.close()



if __name__ == '__main__':
    """
    Run a converter
    """
    
    transfer_gprs()
    
#     import argparse
#     parser = argparse.ArgumentParser(description='Execute converter.')
#     parser.add_argument('-m', action='store', dest='xml_infile', required=True, help='Input SBML file')
#     args = parser.parse_args()
# 
#     xml_infile = args.xml_infile
#     convert_gene_ids_bt(xml_infile)
    