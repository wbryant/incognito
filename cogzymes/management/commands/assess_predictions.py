from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q, Count
from annotation.models import *
from cogzymes.models import *
import sys, os, re


class Command(BaseCommand):
    
    help = 'Validate predictions for a particular development model.'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        if len(args) <> 1:
            print("A single development model ID is required")
            sys.exit(1)
        else:
            try:
                dev_model = Source.objects.get(name=args[0])
                print dev_model
                dev_organism = dev_model.organism
                ref_model = Source.objects.get(organism=dev_organism, reference_model=True)
                print ref_model
            except:
                print("Not a valid development model ID, or could not find single reference model")
                sys.exit(1)
        
        ref_models = Source.objects.filter(reference_model=True).exclude(organism=dev_organism)
        
        
        ## Start with number of times each reaction is predicted
        
        dev_rxns = set(Reaction.objects.filter(model_reaction__source=dev_model).distinct().values_list('name',flat=True))
        ref_rxns = set(Reaction.objects.filter(model_reaction__source=ref_model).distinct().values_list('name',flat=True))
        ref_not_dev = ref_rxns - dev_rxns
        dev_not_ref = dev_rxns - ref_rxns
        
        
        ## a list of lists of reactions separated by number of reference models predicting reaction 
        num_model_predictions_lists = []
        
        num_predictions = 0
        
        num_reactions = 1
        
        while num_reactions > 0:
            
            num_predictions += 1
            
            try:
                preds = zip(*list(Reaction.objects\
                    .filter(
                        model_reaction__reaction_pred__dev_model=dev_model,
                        model_reaction__reaction_pred__status='add'
                    )\
                    .values('model_reaction__reaction_pred__ref_model__name')\
                    .annotate(num_preds=Count('model_reaction__reaction_pred__ref_model__name'))\
                    .order_by()\
                    .filter(num_preds__eq=num_predictions)\
                    .values_list('name', 'num_preds')))[0]
            except:
                preds = []
            
            num_reactions = len(preds)
            
            if num_reactions > 0:
                num_model_predictions_lists.append(preds)
            
            
        """For each number of models predicting each reaction, for the reaction list calculate:
        
        1.    How many are in the reference model for the organism?
        2.    How many are not in the reference model for the organism?"""
        
        for idx, prediction_list in enumerate(num_model_predictions_lists):
            num_models_predicting = idx + 1
            pred_set = set(prediction_list)
            
            num_preds_ref = len(pred_set & ref_not_dev)
            num_preds_not_ref = len(pred_set) - num_preds_ref
            
            print("{:1} models:\t{:5}\t{:5}\t{}".format(
                num_models_predicting,
                num_preds_ref,
                num_preds_not_ref,
                num_preds_ref/float(len(pred_set))
            ))
        
        
        
        
                
                
                