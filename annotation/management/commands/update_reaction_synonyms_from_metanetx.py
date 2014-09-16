from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter, count_lines
from myutils.django.utils import get_model_dictionary

class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        xref_file = '/Users/wbryant/work/BTH/data/metanetx/reac_xref.tsv'
        
        sources = ["metacyc", "bigg", "seed", "chebi", "kegg", "brenda"]
        
        current_synonyms = list(Reaction_synonym.objects.all().values_list('synonym',flat=True))
        
        id_model_dict = get_model_dictionary(Reaction, 'name')
        
        id_source_dict = get_model_dictionary(Source, 'name')
        
        num_lines = count_lines(xref_file)
        
        counter = loop_counter(num_lines, 'Testing all synonyms and adding where not yet exist ...')
        
        f_in = open(xref_file, 'r')
        num_added = 0
        
#         synonym_list = []
#         db_syn_list = []
        
        for line in f_in:
            if line[0] == "#":
                continue
            
            counter.step()
            
            
            [synonym, mnx_id] = line.strip().split('\t')
            
            [db, synonym] = synonym.split(':')
            
            if db in sources:
                if synonym not in current_synonyms:
                    current_synonyms.append(synonym)
                    
                    rxn_syn = Reaction_synonym(
                        synonym = synonym,
                        source = id_source_dict[db],
                        reaction = id_model_dict[mnx_id]
                    )
                    
                    try:
                        rxn_syn.save()
                        num_added += 1
                    except:
                        print("Could not save from '{}'".format(line))
        
        print("{} / {} were added.".format(num_added, num_lines))
        
        counter.stop()            
        f_in.close()
            
            