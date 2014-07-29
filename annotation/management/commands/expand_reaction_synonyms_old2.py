from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter, dict_append
import itertools
from copy import deepcopy 

###! CHECK ALL DB REFERENCES!!!!!!

def get_subsynonyms(synonym, re_terms):
    """Return subsynonyms of synonym with all permutations of expressions in re_terms removed by re.sub."""
    
    subsynonyms = []
    
    for sub_list in itertools.permutations(re_terms):
        subsynonym = deepcopy(synonym)
        for sub_term in sub_list:
            subsynonym = re.sub(sub_term,"",subsynonym)
            if subsynonym != synonym:
                subsynonyms.append(subsynonym)
    
    subsynonyms = list(set(subsynonyms))
    
    return subsynonyms

class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        ## Cycle through command line arguments
        num_args = 0
        for arg in args:
            num_args += 1
        
        ## Remove all previous inferences
        Reaction_synonym.objects.filter(inferred=True).delete()
        
        ## Get all synonym details
        
        synonym_list_orig = Reaction_synonym.objects.filter(inferred=False)\
            .values_list('synonym','reaction__id','source__name')
        
        #print len(synonym_list_orig)
        
        synonym_syn_list = Reaction_synonym.objects.all()\
            .values_list('synonym',flat=True)
        
        print("There are {} synonyms in the current dictionary, looking for alternatives ...".format(synonym_list_orig.count()))
        
        synonym_dict_new = {}
        
        counter = loop_counter(len(synonym_list_orig),"Inferring new synonyms ...")
        
        sub_list = [
            "\-\_",
            "\(\)",
            " ",
            "\([^\)]*\)$"
        ]
        
        for entry in synonym_list_orig:
            
            counter.step()
            
            synonym = entry[0]
            rxn_id = entry[1]
            source = entry[2]
            
            ## Take various steps to create dictionary of lists for new reaction IDs with changes
            
            subsynonyms = get_subsynonyms(synonym, sub_list)
            
            for subsynonym in subsynonyms:
                dict_append(synonym_dict_new,subsynonym,(rxn_id,source))
                
            #print len(subsynonyms)
            
            
        counter.stop()
        
        ## Eliminate all ambiguous synonyms
        
        counter = loop_counter(len(synonym_dict_new),"Populating Reaction_synonym with unambiguous synonyms ...")
        
        for new_synonym in synonym_dict_new:
            
            counter.step()
            
            if new_synonym not in synonym_syn_list:
                
                ## Do all entries for this new synonym refer to the same reaction?
                
                entries = synonym_dict_new[new_synonym]
                rxn_list = []
                for entry in entries:
                    rxn_list.append(entry[0])
                rxn_dup_removed = list(set(rxn_list))
                
                if len(rxn_dup_removed) == 1:
                    ## Unambiguous synonym!  Add to DB with first source
                    
                    try:
                        rxn = Reaction.objects.get(id=entries[0][0])
                        source = Source.objects.get(name=entries[0][1])
                    except:
                        print("Could not get reaction and source for '{}' ...".format(new_synonym))
                        
                    try:
                        synonym_entry = Reaction_synonym(
                                synonym = new_synonym,
                                inferred = True,
                                reaction = rxn,
                                source = source                         
                        )
                        synonym_entry.save()
                    except:
                        print("Could not save reaction_synonym entry for '{}' ...".format(new_synonym))
        
        counter.stop()            
            
        num_synonyms = Reaction_synonym.objects.all().count()
        
        print(" - There are now {} synonyms in Reaction_synonym.".format(num_synonyms))