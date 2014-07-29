from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter
import urllib2
from urllib2 import URLError
from bs4 import BeautifulSoup
from bioservices import UniProt
u = UniProt(verbose=True)

def get_results_from_submission_id(submission_id):
    """ Retrieve all predicted GO terms for submission."""
    
    result_url = 'http://www.sbg.bio.ic.ac.uk/~mwass/combfunc/combfunc_output/'\
                    + submission_id\
                    + '/results.html'
                    
    try:
        ## Get relevant web page connection
        response = urllib2.urlopen(result_url)
    except URLError as e:
        print("'%s' - %s" % (submission_id, e.reason))
        return []
    else:
        ## Get HTML for result
        html = response.read()
        page = BeautifulSoup(html)

        ## Find result table
        tables = page.find_all('table')
        for table in tables:
            if 'Molecular Function Predictions' in table.get_text():
                my_table = table
                break
        
        ## Find results in table
        a_bold = my_table.find_all('a',{'class': 'bold'})
        go_list = [a.get_text() for a in a_bold]
        
        td_bg = my_table.find_all('td',{'bgcolor': 'FFFF00'})
        score_list = [float(td.get_text()) for td in td_bg]
        
        results = zip(go_list, score_list)
        
        return results

def get_gene_locus_from_uniprot_id(uniprot_id):
    """ Retrieve gene locus from Uniprot ID."""
    
    gene = u.mapping(fr='ACC',to='KEGG_ID',query=uniprot_id)[uniprot_id][0]
    gene_locus_tag = gene.split(":")[-1]

    return gene_locus_tag

def get_submission_id_and_uniprot_id(\
            submission_file_path = '/Users/wbryant/work/BTH/data/combfunc/output/submission.log',\
            protein_folder_path = '/Users/wbryant/work/BTH/data/combfunc/input/proteins/'):
    """ Get submission IDs for Combfunc and related UniProt IDs."""
    
    submission_file = open(submission_file_path, 'r')
    
    sub_uniprot = []
    
    for line in submission_file:
        protein_file_name, submission_id = line.split("\t")[0:2]
        
        protein_file = open(protein_folder_path + protein_file_name, 'r')
        first_line = protein_file.readline()
        protein_file.close()
        
        uniprot_id = first_line.split("|")[1]
        
        sub_uniprot.append((submission_id, uniprot_id))
    
    return sub_uniprot 
        

    
class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        ## Cycle through command line arguments
        num_args = 0
        for arg in args:
            num_args += 1
        
        
        sub_uni = get_submission_id_and_uniprot_id()
        
        for sub_uni_pair in sub_uni[0:10]:
            results = get_results_from_submission_id(sub_uni_pair[0])
            locus_tag = get_gene_locus_from_uniprot_id(sub_uni_pair[1])  
        
            print("Gene '%s':\n\n" % locus_tag)
            print results
            print("\n")
            