from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter


class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        ## Get filename from command line.
        
        if len(args) <> 1:
            print("A mapping filename must be supplied with the command.")
            sys.exit(1)
        else:
            map_filename = args[0]


        f_in = open(map_filename, 'r')
        
        ## Get source IDs from 1st line of file 
        
        try:
            model_1_id, model_2_id = f_in.readline().split('\t')
        except:
            print("Model IDs could not be found from first line ...")
            sys.exit(1)
        
        
        ## Check sources
    
        try:
            source_1 = Source.objects.get(name=model_1_id)
            num_reactions = Model_reaction.objects.filter(source=source_1).count()
            organism_1 = source_1.organism
            print("Model 1, ID {}, found, containing {} reactions ...".format(model_1_id, num_reactions))
        except:
            print("Model 1 Source could not be found, exiting ...")
            sys.exit(1)
                    
        try:
            source_2 = Source.objects.get(name=model_2_id)
            num_reactions = Model_reaction.objects.filter(source=source_2).count()
            organism_2 = source_2.organism
            print("Model 2, ID {}, found, containing {} reactions ...".format(model_2_id, num_reactions))
        except:
            print("Model 2 Source could not be found, exiting ...")
            sys.exit(1)
        
        
        ### Get current mapping as dictionary of tuples
        
        mapping_dict = {}
        
        ## MNX mapping
        for mapped_id_pair in Model_reaction.objects\
                            .filter(source=source_1,db_reaction__model_reaction__source=source_2)\
                            .values_list('model_id','db_reaction__model_reaction__model_id'):
            
            model_1_tuple = (mapped_id_pair[0],source_1.name)
            model_2_tuple = (mapped_id_pair[1],source_2.name)
            
            
            mapping_dict[model_1_tuple] = model_2_tuple
            mapping_dict[model_2_tuple] = model_1_tuple
        
        ## Non-MNX mapping (through Reaction_groups)
        for mapped_id_pair in Model_reaction.objects\
                            .filter(source=source_1,model_group__model_reaction__source=source_2)\
                            .values_list('model_id','model_group__model_reaction__model_id'):
            
            model_1_tuple = (mapped_id_pair[0],source_1.name)
            model_2_tuple = (mapped_id_pair[1],source_2.name)
            
            
            mapping_dict[model_1_tuple] = model_2_tuple
            mapping_dict[model_2_tuple] = model_1_tuple
        
        
        ### Run through each mapping in the file
        
        for line in f_in:
            
            try:
                rxn_id_1, rxn_id_2 = line.split("\t")
            except:
                continue
        
            ## if both IDs can be unambiguously found in the DB:
        
            try:
                rxn_1 = Model_reaction.objects.get(source=source_1, model_id=rxn_id_1)
            except:
                try:
                    rxn_1 = Model_reaction.objects.get(source=source_1, name=rxn_id_1)
                except:
                    print("Reaction '{}' from Model 1 could not be identified ...".format(rxn_id_1))
                    continue
        
            try:
                rxn_2 = Model_reaction.objects.get(source=source_2, model_id=rxn_id_2)
            except:
                try:
                    rxn_2 = Model_reaction.objects.get(source=source_2, name=rxn_id_2)
                except:
                    print("Reaction '{}' from Model 2 could not be identified ...".format(rxn_id_2))
                    continue
        
            ## if IDs are not already mapped through Model_reaction_mapping or MNX, 
            ## to either each other or other reactions in same 2 models:
            
            rxn_1_tuple = (rxn_1.model_id, source_1.name)
            rxn_2_tuple = (rxn_2.model_id, source_2.name)
            
            if (not(rxn_1_tuple in mapping_dict) and 
                not(rxn_2_tuple in mapping_dict)):
                
                mapping_dict[rxn_1_tuple] = rxn_2_tuple
                mapping_dict[rxn_2_tuple] = rxn_1_tuple
                
                ## if neither rxn is in a group, create a new group and add them
                
                ## elif one rxn is already in a group, add the other reaction
                
                ## elif both rxns are in groups, merge the groups
                
                
        
        
        
        
        
         