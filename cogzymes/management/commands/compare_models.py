from django.core.management.base import BaseCommand, CommandError
from cogzymes.models import *
from annotation.models import Source, Model_reaction, Model_metabolite, Reaction_group
import sys, os, re

def show_set_overlaps(set_1, set_2, text_summary = None):
    """
    Count unique and overlap items in two sets.
    """
    
    text_summary = text_summary or 'Comparison:'
    
    set_1_only = set_1 - set_2
    set_2_only = set_2 - set_1
    set_both = set_1 & set_2
    
    print("{}:\n".format(text_summary))
    print("{:12}\t{:12}\t{:12}".format("Model 1 Only", "Both Models", "Model 2 Only"))
    print("{:12}\t{:12}\t{:12}\n".format(len(set_1_only), len(set_both), len(set_2_only)))
    
def compare_reactions_and_preds(source_dev, source_ref, source_pred = None, verbose = False):
    """
    Get comparisons of the reaction complements of the two models.
    """
    
    source_pred = source_pred or Source.objects.get(name='iJO1366')
    
    ## Reaction totals without predictions
    
    num_rxns_dev = Model_reaction.objects.filter(source=source_dev).distinct().count()
    num_rxns_ref = Model_reaction.objects.filter(source=source_ref).distinct().count()
    
    num_overlap = Reaction_group.objects\
        .filter(model_reaction__source = source_dev)\
        .filter(model_reaction__source = source_ref)\
        .distinct().count()
    
    print("Reactions (from known mappings):\n")
    print("{:12}\t{:12}\t{:12}".format("Model 1 Only", "Both Models", "Model 2 Only"))
    print("{:12}\t{:12}\t{:12}\n".format(num_rxns_dev-num_overlap, num_overlap, num_rxns_ref-num_overlap))
    
    
    ## Predicted reactions
    
    num_possible_in_ref = Reaction_group.objects\
        .filter(model_reaction__source=source_ref)\
        .filter(model_reaction__source=source_pred)\
        .exclude(model_reaction__source=source_dev)\
        .distinct().count()
        
    num_found_by_pred = Reaction_group.objects\
        .filter(model_reaction__source=source_ref)\
        .filter(model_reaction__source=source_pred)\
        .exclude(model_reaction__source=source_dev)\
        .filter(mapping__reaction__reaction_pred__dev_model=source_dev,\
                mapping__reaction__reaction_pred__ref_model=source_pred,\
                mapping__reaction__reaction_pred__status='add')\
        .distinct().count()
    
    print("Number of possible predictions found = {}/{} ({:.0%})\n".format(
        num_found_by_pred,
        num_possible_in_ref,
        num_found_by_pred/float(num_possible_in_ref)))
    
    
    if verbose:
        rxns_possible_in_ref = Model_reaction.objects\
            .filter(source=source_ref)\
            .filter(mapping__model_reaction__source=source_pred)\
            .exclude(mapping__model_reaction__source=source_dev)\
            .distinct()
    
        print("{:55} - {:10}{:11}".format('Name', 'Model ID', 'Mapped Mets'))
         
        for ref_rxn in rxns_possible_in_ref:
            if Reaction_group.objects\
                .filter(model_reaction=ref_rxn)\
                .filter(model_reaction__source=source_pred)\
                .exclude(model_reaction__source=source_dev)\
                .filter(mapping__reaction__reaction_pred__dev_model=source_dev,\
                    mapping__reaction__reaction_pred__ref_model=source_pred,\
                    mapping__reaction__reaction_pred__status='add')\
                .distinct().count() > 0:
                
                found_by_pred = '*'
            else:
                found_by_pred = ''
            
            ## Get number of crossover metabolites
            
            num_mets = ref_rxn.metabolites.all().count()
            num_crossover_mets = ref_rxn.metabolites\
                .filter(db_metabolite__model_metabolite__source=source_dev)\
                .distinct().count()
            
            print("{:55} - {:9}{} {}/{}"\
                .format(
                    ref_rxn.name, 
                    ref_rxn.model_id, 
                    found_by_pred,
                    num_crossover_mets,
                    num_mets))
            

class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        if len(args) > 4:
            print("Too many arguments!")
            sys.exit(1)
        else:
            try:
                model_1_name = args[0]
                model_2_name = args[1]
                source_1 = Source.objects.get(name=model_1_name)
                source_2 = Source.objects.get(name=model_2_name)                
            except:
                print("Models could not be identified, check IDs")
                sys.exit(1)
            
            try:
                model_pred_name = args[2]
            except:
                model_pred_name = 'iJO1366'
                print("Using default prediction model ({}) ...".format(model_pred_name))
        
            try:
                source_pred = Source.objects.get(name=model_pred_name)
            except:
                print("Model ID '{}' could not be found, exiting ...".format(model_pred_name))
                sys.exit(1)

            try:
                args[3]
                verbose = True
            except:
                verbose = False
        
        
        ## How many cogzymes overlap?
        
        cogzymes_1 = set([cogzyme for cogzyme in Cogzyme.objects.filter(enzymes__source=source_1).distinct()])
        cogzymes_2 = set([cogzyme for cogzyme in Cogzyme.objects.filter(enzymes__source=source_2).distinct()])
        show_set_overlaps(cogzymes_1, cogzymes_2, 'Cogzymes in each model')
        
        
        ## Reactions and predictions
        
        print source_1
        print source_2
        print source_pred
        
        compare_reactions_and_preds(source_1, source_2, source_pred, verbose)
        

                
                
                