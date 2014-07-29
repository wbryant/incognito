from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from annotation.management.commands.model_integration_tools import get_subsynonyms
from myutils.general.utils import loop_counter, dict_append


class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ Take all Metabolite_synonym entries and find unique shortenings to expand the synonym pool.
            
        """ 
        
        ## Cycle through command line arguments
        num_args = 0
        for arg in args:
            num_args += 1
        
        ## Remove all previous inferences
        Metabolite_synonym.objects.filter(inferred=True).delete()
        
        ## Get all synonym details
        
        synonym_list_orig = Metabolite_synonym.objects.filter(inferred=False)\
            .values_list('synonym','metabolite__id','source__name')
        
        synonym_syn_list = Metabolite_synonym.objects.all()\
            .values_list('synonym',flat=True)
        
        print("There are {} synonyms in the current dictionary, looking for alternatives ...".format(synonym_list_orig.count()))
        
        synonym_dict_new = {}
        
        counter = loop_counter(len(synonym_list_orig),"Inferring new synonyms ...")
        
        sub_list = [
            "[-_]",
            "[\(\)]",
            " ",
            "\([^\)]*\)$"
        ]
        
        for entry in synonym_list_orig:
            
            counter.step()
            
            synonym = entry[0]
            met_id = entry[1]
            source = entry[2]
            
            ## Take various steps to create dictionary of lists for new reaction IDs with changes
            
            subsynonyms = get_subsynonyms(synonym, sub_list)
            
            for subsynonym in subsynonyms:
                dict_append(synonym_dict_new,subsynonym,(met_id,source))
        
        counter.stop()
        
        ## Eliminate all ambiguous synonyms
        
        counter = loop_counter(len(synonym_dict_new),"Populating Metabolite_synonym with unambiguous synonyms ...")
        
        for new_synonym in synonym_dict_new:
            
            counter.step()
            
            if new_synonym not in synonym_syn_list:
                
                ## Do all entries for this new synonym refer to the same metabolite?
                
                entries = synonym_dict_new[new_synonym]
                met_list = []
                for entry in entries:
                    met_list.append(entry[0])
                met_dup_removed = list(set(met_list))
                
                if len(met_dup_removed) == 1:
                    ## Unambiguous synonym!  Add to DB with first source
                    
                    try:
                        met = Metabolite.objects.get(id=entries[0][0])
                        source = Source.objects.get(name=entries[0][1])
                    except:
                        print("Could not get metabolite and source for '{}' ...".format(new_synonym))
                        
                    try:
                        synonym_entry = Metabolite_synonym(
                                synonym = new_synonym,
                                inferred = True,
                                metabolite = met,
                                source = source                         
                        )
                        synonym_entry.save()
                    except:
                        print("Could not save metabolite_synonym entry for '{}' ...".format(new_synonym))
        
        counter.stop()            
            
        num_synonyms = Metabolite_synonym.objects.all().count()
        
        print(" - There are now {} synonyms in Metabolite_synonym.".format(num_synonyms))