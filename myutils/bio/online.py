'''
Created on 14 Jul 2014

@author: wbryant
'''

import re, sys
from Bio import Entrez
from time import sleep


def get_loci_from_protein_gis(protein_gi_list, locus_pattern, line_limit = 20):
    """
    Take a list of protein GIs and use Bio.Entrez to retrieve the relevant gene locus tags.
    
    'locus_pattern' will identify the tag within the records downloaded by Bio.Entrez.
    """

    Entrez.email = "wbryant@imperial.ac.uk"
    
    
    ## There is a maximum length for a URI (2000?), so if too many, the requests must be split into groups
    ##  - Given the lengths of GIs, limit number submitted to 600 per transaction
    ## N.B. limit to 2 requests per second - which means one iteration per second
    
    max_gis_per_submission = 600
    
    protein_gi_gene_gi_dict = {}
    gene_gi_list = []
    proteins_found_list = []
    genes_found_list = []
    gene_gi_locus_tag_dict = {}
    protein_gis_failed = []
    gene_gis_failed = []
    
    for idx in range(0, len(protein_gi_list), max_gis_per_submission):
        
        print("Waiting for next query ...")
        sleep(1)
        protein_gi_sublist = protein_gi_list[idx:idx + max_gis_per_submission]
    
        ## Look for a gene mapping for each protein GI
        
        handle = Entrez.elink(db="gene", dbfrom="protein", id=protein_gi_sublist)
        records = Entrez.read(handle)
        
        
        ## For each protein GI with a record (that mapped), pull out the gene GI
        
        gene_gi_list = []
        for record in records:
            
            protein_gi = record['IdList'][0]
            
            try:
                gene_gi = record['LinkSetDb'][0]['Link'][0]['Id']
            except:
                protein_gis_failed.append(protein_gi)
                continue
#                 print("There is at least one incorrect input GI ('{}'), please check ...".format(protein_gi))
#                 sys.exit(1)
            
            gene_gi_list.append(gene_gi)
            protein_gi_gene_gi_dict[protein_gi] = gene_gi
            proteins_found_list.append(protein_gi)
        
        
        ## Find the Genbank entry for each gene GI
             
        handle2 = Entrez.efetch(db="gene", id=gene_gi_list, rettype="gb", retmode="xml")
        gene_records = Entrez.read(handle2)
        
        
        ## For each found Genbank entry find the relevant locus tag if it exists
        
        for gene_record in gene_records:
                
            ## Note gene GI number
            
            try:
                gene_gi = gene_record['Entrezgene_track-info']['Gene-track']['Gene-track_geneid']
            except:

                continue
            
            genbank_string = str(gene_record)
            
            
            ## Look for locus tag in gene record
            
            try:
                locus_tag = re.search(locus_pattern,genbank_string).group(0)
                genes_found_list.append(locus_tag)
                gene_gi_locus_tag_dict[gene_gi] = locus_tag
            except:
                gene_gis_failed.append(gene_gi)
                continue
        
    
    ## Create output dictionary and failed IDs
    
    protein_gi_locus_tag_dict = {}
    p_gis_failed = []
    g_gis_failed = []
    for p_gi in protein_gi_list:
        if p_gi in protein_gi_gene_gi_dict:
            if protein_gi_gene_gi_dict[p_gi] in gene_gi_locus_tag_dict:
                protein_gi_locus_tag_dict[p_gi] = gene_gi_locus_tag_dict[protein_gi_gene_gi_dict[p_gi]]
            else:
                g_gis_failed.append((p_gi, protein_gi_gene_gi_dict[p_gi]))
        else:
            p_gis_failed.append((p_gi))
    
    
    errors = [p_gis_failed, g_gis_failed, protein_gis_failed, gene_gis_failed]
    
    return protein_gi_locus_tag_dict, errors


def get_locus_from_protein_gi(protein_gi, locus_pattern, line_limit = 20):
    """
    Take a protein GI and use Bio.Entrez to retrieve the relevant gene locus tag.
    
    'locus_pattern' will identify the tag within the records downloaded by Bio.Entrez.
    """

    Entrez.email = "wbryant@imperial.ac.uk"
    
    handle = Entrez.elink(db="gene", dbfrom="protein", id=protein_gi)
    record = Entrez.read(handle)
    
    try:
        gene_gi = record[0]['LinkSetDb'][0]['Link'][0]['Id']
    except:
        print("No gene GI found for '{}'".format(protein_gi))
        return None
    
    handle2 = Entrez.efetch(db="gene", id=gene_gi, rettype="gb", retmode="text")
    gene_gb_line = handle2.readline().strip()
    
    lines_read = 1
    
    while True:
        if 'Other Aliases' in gene_gb_line:
            locus_tags = re.findall(locus_pattern, gene_gb_line)
            if len(locus_tags) == 1:
                return locus_tags[0]
            elif len(locus_tags) == 0:
                print("No locus tags matching '{}' found.".format(locus_pattern))
                return None
        
        if lines_read == line_limit:
            print("'Other Aliases' not found in first {} lines.".format(line_limit))
            return None
        
        gene_gb_line = handle2.readline().strip()
        lines_read += 1
        
    
        



if __name__ == '__main__':
    pass