from django.core.management.base import BaseCommand, CommandError
from cogzymes.models import *
from annotation.models import Source, Model_reaction, Reaction_group
import sys, os, re
from django.db.models import Count



class Command(BaseCommand):
    
    help = 'Show details of a particular metabolic model'
        
    def handle(self, *args, **options):
        
        """ Show details of a particular metabolic model
            
        """ 
        
        ## Cycle through command line arguments
        
        if len(args) > 1:
            print("Only model ID should be passed as argument, exiting ...")
            sys.exit(1)
        else:
            try:
                model_id = args.pop[0]
                model_source = Source.objects.get(name=model_id)
            except:
                print("Model ID not given/found, using default ...")
                model_id = 'iJO1366'
                model_source = Source.objects.get(name=model_id)
        
        
        print("Model ID '{}' details:\n".format(model_source.name))
        
        ## Number of reactions
        
        num_rxns = Model_reaction.objects.filter(source=model_source).count()
        print("{} reactions.".format(num_rxns))
    
        
        ## Number of reactions mapped to DB
        
        num_rxns_mapped_to_db = Model_reaction.objects.filter(source=model_source, db_reaction__isnull=False).count()
        print("{} reactions mapped to DB.".format(num_rxns_mapped_to_db))
        
        
        ## Number of reactions mapped to at least two other models
        
        num_rxns_mapped_to_at_least_2_others = Reaction_group.objects\
            .filter(model_reaction__source = model_source)\
            .exclude(model_reaction__source = model_source)\
            .count()
            
        
        
        
        
        ## Number of adding predictions
        ## - number with DB reaction association
        ## Number of removing predictions
        
        
        
        
        ## Number of Cogzymes
        
        
        
        

                
                
                