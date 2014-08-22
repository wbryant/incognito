from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter
from myutils.general.utils import dict_append

class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        syn_mets = Metabolite_synonym.objects.all().values_list('synonym','metabolite__id')
        syn_met_list = [syn_met for syn_met in syn_mets]
        syn_met_dict = {}
        for syn_met in syn_met_list:
            dict_append(syn_met_dict, syn_met[0], syn_met[1])
        
        dupe_syn_list = []
        for syn in syn_met_dict:
            met_set = set(syn_met_dict[syn])
            if len(met_set) > 1:
#                 print syn, syn_met_dict[syn]
#                 met_list = list(met_set) 
#                 met_num_list = sorted([int(met_id[4:]) for met_id in met_list])
#                 if ((met_num_list[0] < 10000) and (met_num_list[1] > 10000)):
#                     met_keep = 'MNXM' + str(met_num_list[0])
# #                     print(" - {}".format(met_keep))
#                 else:
#                     met_keep = ''
                    
#                 Metabolite_synonym.objects\
#                     .filter(synonym=syn)\
#                     .exclude(metabolite__id=met_keep)\
#                     .delete()
                
#                 for dsr in del_synonym_reactions:
#                     print dsr
                
                dupe_syn_list.append(syn)
                
        print("Number of ambiguous synonyms = {}".format(len(dupe_syn_list)))
