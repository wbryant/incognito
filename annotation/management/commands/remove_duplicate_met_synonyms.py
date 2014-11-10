from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter, dict_append, preview_dict


class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        syn_dict = {}
        
        for syn in Metabolite_synonym.objects.all().prefetch_related('metabolite'):
            syn_name = syn.synonym.lower()
            dict_append(syn_dict,syn_name,syn.metabolite)
        
        num_syns = 0
        synonym_dels = []
        for syn_name, met_list in syn_dict.iteritems():
            met_list = list(set(met_list))
            
            num_mets = len(met_list)
            
            if num_mets > 1:
                num_syns += 1
                print("-{}".format(syn_name.encode('utf-8')))
                mets_undeleted = []
                synonyms_undeleted = []
                for synonym in Metabolite_synonym.objects\
                                    .filter(synonym=syn_name, metabolite__in=met_list)\
                                    .prefetch_related('metabolite'):
                    
                    if synonym.metabolite.name.lower() != syn_name.lower():
                        print("\t\t- {}, {} ({})".format(
                            synonym.pk,
                            synonym.metabolite.name.encode('utf-8'),
                            synonym.metabolite.pk
                            ))
                        synonym_dels.append(synonym)
                    else:
                        mets_undeleted.append(synonym.metabolite)
                        synonyms_undeleted.append(synonym)

#                     print("\t{}- {}, {} ({})".format(
#                         star,
#                         synonym.pk,
#                         synonym.metabolite.name.encode('utf-8'),
#                         synonym.metabolite.pk
#                         ))     
                
                if len(set(mets_undeleted)) > 1:
                    ## All must be deleted because of duplicate metabolite name
                    print("- {} duplicate names".format(syn_name.encode('utf-8')))
                    for synonym in synonyms_undeleted:
                        print("\t\t- {}, {} ({})".format(
                            synonym.pk,
                            synonym.metabolite.name.encode('utf-8'),
                            synonym.metabolite.pk
                            ))     
                        synonym_dels.append(synonym)
        
        print num_syns
        print len(set(synonym_dels))
        
#         for synonym in synonym_dels:
#             print("deleting <{}>".format(synonym))
#             synonym.delete()
                        
