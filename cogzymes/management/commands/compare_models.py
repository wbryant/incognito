from django.core.management.base import BaseCommand, CommandError
from cogzymes.models import *
from annotation.models import Source, Model_reaction, Model_metabolite
import sys, os, re


class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        if len(args) <> 2:
            print("Model IDs not given, exiting ...")
            sys.exit(1)
        else:
            try:
                model_1_name = args[0]
                source_1 = Source.objects.get(name=model_1_name)
            except:
                print("Model ID '{}' could not be found, exiting ...".format(model_1_name))
                sys.exit(1)
            try:
                model_2_name = args[1]
                source_2 = Source.objects.get(name=model_2_name)
            except:
                print("Model ID '{}' could not be found, exiting ...".format(model_2_name))
                sys.exit(1)
        

        ## How many cogzymes overlap?
        
        cogzymes_1 = set([cogzyme for cogzyme in Cogzyme.objects.filter(enzymes__source=source_1).distinct()])
        cogzymes_2 = set([cogzyme for cogzyme in Cogzyme.objects.filter(enzymes__source=source_2).distinct()])
        
        cz_1_only = cogzymes_1 - cogzymes_2
        cz_2_only = cogzymes_2 - cogzymes_1
        cz_both = cogzymes_1 & cogzymes_2
        
        print("{:12}\t{:12}\t{:12}".format("Model 1 Only", "Both Models", "Model 2 Only"))
        print("{:12}\t{:12}\t{:12}".format(len(cz_1_only), len(cz_both), len(cz_2_only)))
        
        
        
        
        
        

                
                
                