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
            model_1_id, model_2_id = f_in.readline().strip().split('\t')
        except:
            print("Model IDs could not be found from first line ...")
            sys.exit(1)
        
        
        ## Check sources
    
        try:
            source_1 = Source.objects.get(name=model_1_id)
            organism_1 = source_1.organism
            num_reactions = Model_reaction.objects.filter(source=source_1).count()
            num_mapped = Model_reaction.objects.filter(reaction_mapped__isnull=False, source=source_1).count()
            print("Model 1, ID {}, found, containing {} reactions ({} of which are mapped) ..."
                  .format(model_1_id, num_reactions, num_mapped))
        except:
            print("Model 1 Source could not be found, exiting ...")
            sys.exit(1)
                    
        try:
            source_2 = Source.objects.get(name=model_2_id)
            organism_2 = source_2.organism
            num_reactions = Model_reaction.objects.filter(source=source_2).count()
            num_mapped = Model_reaction.objects.filter(reaction_mapped__isnull=False, source=source_2).count()
            print("Model 2, ID {}, found, containing {} reactions ({} of which are mapped) ..."
                  .format(model_2_id, num_reactions, num_mapped))
        except:
            print("Model 2 Source could not be found, exiting ...")
            sys.exit(1)
        
        
        ### Get current mapping as dictionary of tuples
        
        mapping_dict = {}
        
#         ## MNX mapping
#         for mapped_id_pair in Model_reaction.objects\
#                             .filter(source=source_1,db_reaction__model_reaction__source=source_2)\
#                             .values_list('model_id','db_reaction__model_reaction__model_id'):
#             
#             model_1_tuple = (mapped_id_pair[0],source_1.name)
#             model_2_tuple = (mapped_id_pair[1],source_2.name)
#             
#             
#             mapping_dict[model_1_tuple] = model_2_tuple
#             mapping_dict[model_2_tuple] = model_1_tuple
        
        ## Get all mappings from Reaction Groups
        for mapped_id_pair in Model_reaction.objects\
                            .filter(source=source_1,mapping__model_reaction__source=source_2)\
                            .values_list('model_id','mapping__model_reaction__model_id'):
            
            model_1_tuple = (mapped_id_pair[0],source_1.name)
            model_2_tuple = (mapped_id_pair[1],source_2.name)
            
            
            mapping_dict[model_1_tuple] = model_2_tuple
            mapping_dict[model_2_tuple] = model_1_tuple
        
        
        ## get / create mapping method
        
        try:
            method = Method.objects.get(name='manual')
        except:
            method = Method(name='manual')
            method.save()
        
        ### Run through each mapping in the file
        
        for line in f_in:
            
            try:
                rxn_id_1, rxn_id_2 = line.strip().split("\t")
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
        
            ## if IDs are not already in a Reaction Group, add them / create group as appropriate
            
            rxn_1_tuple = (rxn_1.model_id, source_1.name)
            rxn_2_tuple = (rxn_2.model_id, source_2.name)
            
            if (not(rxn_1_tuple in mapping_dict) and 
                not(rxn_2_tuple in mapping_dict)):
                
                mapping_dict[rxn_1_tuple] = rxn_2_tuple
                mapping_dict[rxn_2_tuple] = rxn_1_tuple
                
                ## if neither rxn is in a group, create a new group and add them
                
                try:
                    group_rxn_1 = Reaction_group.objects.get(model_reaction=rxn_1)
                except:
                    group_rxn_1 = None
                    
                try:
                    group_rxn_2 = Reaction_group.objects.get(model_reaction=rxn_2)
                except:
                    group_rxn_2 = None
                    
                if (not group_rxn_2 and not group_rxn_1):
                    ## Create and populate new group
                    
                    new_group = Reaction_group(
                        name = "{} ({})".format(rxn_1.name,rxn_1.source.name)
                    )
                    new_group.save()
                    
                    rxn_1_mapping = Mapping(
                        group = new_group,
                        reaction = rxn_1,
                        method = method
                    )
                    rxn_1_mapping.save()
                    
                    rxn_2_mapping = Mapping(
                        group = new_group,
                        reaction = rxn_2,
                        method = method
                    )
                    rxn_2_mapping.save()                    
                    
                elif group_rxn_1 and group_rxn_2:
                    ## Merge groups
                    
                    if (group_rxn_1.name.startswith("MNX") and group_rxn_2.name.startswith("MNX")):
                        print("MNX thinks the reactions '{} ({})' and '{} ({})' are different:"
                              .format(rxn_1.name, rxn_1.source.name, rxn_2.name, rxn_2.source.name))
                        
                        print(" - Reaction 1 ({}): {}".format(rxn_1.db_reaction.name, rxn_1.db_reaction.equation()))
                        print(" - Reaction 2 ({}): {}\n".format(rxn_2.db_reaction.name, rxn_2.db_reaction.equation()))
                        ## DETAILS of differences!
                        
                        continue
                    elif group_rxn_2.name.startswith("MNX"):
                        merge_group = group_rxn_2
                        removal_group = group_rxn_1
                    else:
                        ## By default use Reaction 1's group to merge
                        merge_group = group_rxn_1
                        removal_group = group_rxn_2
                    
                    for mapping in Mapping.objects.filter(group=removal_group):
                        mapping.group = merge_group
                        mapping.method = method
                        mapping.save()
                    
                    removal_group.delete()
                
                else:
                    ## Add ungrouped reaction to other reaction's group
                    
                    if group_rxn_1:
                        add_group = group_rxn_1
                        add_rxn = rxn_2
                    else:
                        add_group = group_rxn_2
                        add_rxn = rxn_1
                    
                    mapping = Mapping(
                        group = add_group,
                        reaction = add_rxn,
                        method = method
                    )
                    mapping.save()
                    
        print("Mapping complete")          
        num_mapped = Model_reaction.objects.filter(reaction_mapped__isnull=False, source=source_1).count()  
        print("Model 1 ({}) now contains {} mapped reactions and"
                  .format(model_1_id, num_mapped))
        num_mapped = Model_reaction.objects.filter(reaction_mapped__isnull=False, source=source_2).count()  
        print("Model 2 ({}) now contains {} mapped reactions."
                  .format(model_2_id, num_mapped))