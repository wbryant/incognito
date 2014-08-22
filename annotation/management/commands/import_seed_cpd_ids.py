from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter, dict_append, count_lines
from myutils.django.utils import get_model_dictionary

def find_cpd_metabolite(synonym_list):
    """
    Try to establish metabolite from synonym list.
    """
    
    metabolites = Metabolite.objects\
        .filter(metabolite_synonym__synonym__in=synonym_list)\
        .distinct()
        
    if len(metabolites) == 1:
        metabolite = metabolites[0]
    else:
        return None
    
    return metabolite


def find_cpd_metabolite_dict(synonym_list, syn_met_dict, met_db_dict):
    """
    Try to establish metabolite from synonym list
    using a synonym_met dict
    """
    mets = []
    
    for synonym in synonym_list:
        try:
            mets.append(syn_met_dict[synonym])
        except:
            pass
    
    mets_list = list(set(mets))
    
    if len(mets_list) <> 1:
        return None
    else:
        return Metabolite.objects.get(id=mets_list[0])
        
    
def add_cpd_to_synonyms(seed_id_line, source, syn_met_dict, met_db_dict):
    """
    Take seed_id_line and attempt to add cpd_id to Metabolite_synonym
    """
    
    seed_id_cols = seed_id_line.split('\t')
    cpd_id = seed_id_cols[0]
    synonym_set = seed_id_cols[1]
    synonym_list = synonym_set.split(';')
    
    metabolite = find_cpd_metabolite_dict(synonym_list, syn_met_dict, met_db_dict)
    
#     if metabolite:
#         print("{} - {}".format(cpd_id, metabolite.id))
#     else:
#         print("   - failed: {} - {}".format(cpd_id, synonym_set))
    
    if metabolite:
        met_synonym = Metabolite_synonym(
            synonym = cpd_id,
            metabolite = metabolite,
            source = source
        )
        met_synonym.save()


def get_synonym_met_dict():
    
    synonym_met_dict = {}
    
    synonym_met_pairs = Metabolite_synonym.objects\
        .all()\
        .values_list('synonym', 'metabolite_id')
    
    
    for pair in synonym_met_pairs:
        dict_append(synonym_met_dict, pair[0], pair[1], ignore_duplicates = True)
    
    new_dict = {}
    
    for key in synonym_met_dict:
        if len(synonym_met_dict[key]) == 1:
            new_dict[key] = synonym_met_dict[key][0]
    
    return new_dict 
    

def add_cpd_synonyms_from_datafile(filename = '/Users/wbryant/work/cogzymes/data/SEED/SEED_met_table.csv'):
    """
    Take file from SEED and add cpd IDs to Metabolite_synonym if they can be identified
    """
    
    
    num_syns_added = 0
    num_syns_tested = 0
    
    source = Source.objects.get(name='seed')
    
    met_db_dict = get_model_dictionary(Metabolite, 'id')
    syn_met_dict = get_synonym_met_dict()
    
    counter = loop_counter(count_lines(filename), 'Adding CPD IDs to database')
    
    f_in = open(filename, 'r')
    for line in f_in:
        counter.step()
        add_cpd_to_synonyms(line, source, syn_met_dict, met_db_dict)
    
    counter.stop()
   
    
class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        add_cpd_synonyms_from_datafile()
        
        pass