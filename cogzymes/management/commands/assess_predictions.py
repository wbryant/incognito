from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q, Count
from annotation.models import *
from cogzymes.models import *
from myutils.general.utils import dict_append, preview_dict
import sys, os, re
from collections import Counter

from itertools import groupby, product
from operator import itemgetter
from myutils.general.mnxref_reac_extract import Rxn_ids

def evaluate_prediction_quality(pred_set, ref_set, description = "Quality scores"):
    
    if len(pred_set) == 0:
        return []
    
    num_preds_ref = len(pred_set & ref_set)
    num_preds_not_ref = len(pred_set) - num_preds_ref
    
    print("{}:\t{:5}\t{:5}\t{:.3f}".format(
        description,
        num_preds_ref,
        num_preds_not_ref,
        num_preds_ref/float(len(pred_set))
    )) 
    
def bsu_correction(bsu_num):
    """Many BSU gene names have an excess 0 at the end, making consecutive inferences difficult.
    Remove this zero.  This is not perfect as a few genes have a non-zero last digit - ignore these for now.
    """
    
    bsu_str = str(bsu_num)
    
    if bsu_str[-1] == '0':
        bsu_num = int(bsu_str[:-1])
    
    return bsu_num
     

def get_valid_preds(ref_model, dev_model = None):
    """Return set of reactions that are to be tested against."""
    
    dev_rxns = set(Reaction.objects.filter(model_reaction__source=dev_model).distinct().values_list('name',flat=True))
    ref_rxns = set(Reaction.objects.filter(model_reaction__source=ref_model).distinct().values_list('name',flat=True))
    ref_not_dev = ref_rxns - dev_rxns
    dev_not_ref = dev_rxns - ref_rxns
    
    return ref_not_dev, dev_rxns, ref_rxns, dev_not_ref

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

        ref_not_dev, dev_rxns, ref_rxns, dev_not_ref = get_valid_preds(ref_model, dev_model)
        
        description = "\nInitial model quality"
        evaluate_prediction_quality(dev_rxns, ref_rxns, description)
        
        ## Get all predicted additional reactions, along with number of models predicting those reactions
        
        pred_counts = Counter(zip(*list(
            Reaction_pred.objects
            .filter(dev_model=dev_model, status='add')
            .values_list('reaction__db_reaction__name','ref_model__name')
            .distinct()
        ))[0]) 
        
        pred_set = set(pred_counts.keys())
             
        num_preds_ref = len(pred_set & ref_not_dev)
        num_preds_not_ref = len(pred_set) - num_preds_ref
         
        print("\nAll predictions:\t{:5}\t{:5}\t{:.3f}".format(
            num_preds_ref,
            num_preds_not_ref,
            num_preds_ref/float(len(pred_set))
        ))
        
        
        ## Look at different numbers of predictions
        
        num_model_predictions_lists = []
        
        num_model_predictions_values = sorted(list(set(pred_counts.values())))
        
        for num_models in num_model_predictions_values:
            counted_pred_list = []
            for rxn in pred_counts:
                if pred_counts[rxn] == num_models:
                    counted_pred_list.append(rxn)
            
            num_model_predictions_lists.append([num_models, counted_pred_list])
        
        
        for pred_data in num_model_predictions_lists:
            pred_set = pred_set - set(pred_data[1])
            if len(pred_set) == 0:
                break
             
            num_preds_ref = len(pred_set & ref_not_dev)
            num_preds_not_ref = len(pred_set) - num_preds_ref
             
            
            print("{:1} or more models:\t{:5}\t{:5}\t{:.3f}".format(
                pred_data[0] + 1,
                num_preds_ref,
                num_preds_not_ref,
                num_preds_ref/float(len(pred_set))
            ))        

        
        ## Look at each prediction to see whether enzymes could be made up from adjacent genes in dev genome
        ##  - Assumes sequential numbering of all genes at end of locus tag
        print("\nCandidate operon search:")
        
        predictions = Reaction_pred.objects.filter(dev_model=dev_model)
        
        preds_with_candidate_operons = []
        preds_without_candidate_operons = []
        
        more_preds_needed = True
        num_preds_multi = 0
        
        for prediction in predictions:
            
            if not more_preds_needed:
                break
            
            if num_preds_multi >= 10000:
                more_preds_needed = False
            if "," in prediction.cogzyme.name:
#                 print("\n")
#                 print prediction.cogzyme.name
                num_preds_multi += 1
                ## More than one COG in this COGzyme, so look for adjacent genes
                locus_cog_data = Gene.objects\
                    .filter(
                        organism__source=dev_model,
                        cogs__cogzyme=prediction.cogzyme)\
                    .values('locus_tag','cogs__name').distinct()
                
                ## Create a dictionary of locus tags > COGs, nums > locus tags
                locus_cog_dict = {}
                locus_num_tag_dict = {}
                locus_num_list = []
                locus_nums_not_mult10 = 0
#                 print locus_cog_data
                for locus_cog in locus_cog_data:
                    dict_append(locus_cog_dict,locus_cog['locus_tag'],locus_cog['cogs__name'])
                    locus = locus_cog['locus_tag']
#                     print locus
                    try:
                        locus_num = int(re.search('(\d+)[^0-9]*$',locus).group(1))
                        if locus_num%10 == 0:
                            locus_num = bsu_correction(locus_num)
                        else:
                            locus_nums_not_mult10 += 1
                    except:
                        continue
                    locus_num_tag_dict[locus_num] = locus
                    locus_num_list.append(locus_num)
                               
                locus_nums_sorted = sorted(list(set(locus_num_list)))
               
                ## COG set for COGzyme
                cogzyme_cog_set = set(prediction.cogzyme.name.split(","))
                
                
                ## Look for sets of consecutive numbers (loci) of the correct length and test against COGzyme COGs
                operon_candidate = False
                for idx, locus_group in groupby(enumerate(locus_nums_sorted), lambda (i,x):i-x):
                    ## Get all COGs from this set of loci, do they contain the cogzyme?
                    cog_list = []
                    gene_list = []
                    for locus_num in locus_group:
                        locus_num = locus_num[1]
                        tag = locus_num_tag_dict[locus_num]
                        gene_list.append(tag)
                        for cog in locus_cog_dict[tag]:
                            cog_list.append(cog)
 
                    locus_cog_set = set(cog_list)
                    gene_set = set(gene_list)
                    
                    if (cogzyme_cog_set <= locus_cog_set) & (len(cogzyme_cog_set) >= 3):

                        
                        ## COGs can be obtained for this cogzyme from this set of adjacent loci
                        operon_candidate = True
                        
                        preds_with_candidate_operons.append(prediction.reaction.db_reaction.name)
                        
#                         if prediction.reaction.db_reaction.name in ref_not_dev:
#                             print("\nSubset found for prediction {}:".format(prediction.pk))
#                          
#                             print("cogzyme_cog_set for genes:")
#                             print cogzyme_cog_set
#     
#                             print("gene_set:")
#                             print gene_set
#                             for locus in gene_set:
#                                 print locus, locus_cog_dict[locus]
#                             print("--> correct prediction")
#                         else:
#                             print("--> incorrect prediction")
                        
                        
                        
                        
                        ## Break, but if actual operons are required, will have to run through all groups of adjacent loci
                        break
                
                if not operon_candidate:
                    preds_without_candidate_operons.append(prediction.reaction.db_reaction.name)
                        
        ## Test predictions against reference model
        
        p_w_co = set(preds_with_candidate_operons)
        p_wo_co = set(preds_without_candidate_operons)
        
        ## p_w_co
        pred_set = p_w_co
        num_preds_ref = len(pred_set & ref_not_dev)
        num_preds_not_ref = len(pred_set) - num_preds_ref
        
        print("With candidate operons:\t{:5}\t{:5}\t{:.3f}".format(
            num_preds_ref,
            num_preds_not_ref,
            num_preds_ref/float(len(pred_set))
        ))                
        
        ## p_wo_co
        pred_set = p_wo_co
        num_preds_ref = len(pred_set & ref_not_dev)
        num_preds_not_ref = len(pred_set) - num_preds_ref
        
        print("No candidate operons:\t{:5}\t{:5}\t{:.3f}".format(
            num_preds_ref,
            num_preds_not_ref,
            num_preds_ref/float(len(pred_set))
        ))                
                
                
        ## Which is the best model for prediction?
        print("\nResults for individual models:")
        
        for ref_model in ref_models:
            pred_set = set(
                Reaction_pred.objects
                .filter(dev_model=dev_model, ref_model=ref_model, status='add')
                .values_list('reaction__db_reaction__name', flat=True)
                .distinct()
            )
            
            description = "{} ({})".format(ref_model.name, ref_model.organism.taxonomy_id)
            
            evaluate_prediction_quality(pred_set, ref_not_dev, description)
        
        ## REMOVAL OF REACTIONS
        
        ## Get all predicted removed reactions, along with number of models predicting those removals
        print("\nREMOVAL PREDICTIONS")
        
        pred_counts = Counter(zip(*list(
            Reaction_pred.objects
            .filter(dev_model=dev_model, status='rem')
            .values_list('reaction__db_reaction__name','ref_model__name')
            .distinct()
        ))[0]) 
        
        pred_set = set(pred_counts.keys())
             
        num_preds_ref = len(pred_set & dev_not_ref)
        num_preds_not_ref = len(pred_set) - num_preds_ref
         
        print("\nAll predictions:\t{:5}\t{:5}\t{:.3f}".format(
            num_preds_ref,
            num_preds_not_ref,
            num_preds_ref/float(len(pred_set))
        ))


        ## Look at different numbers of predictions
        
        num_model_predictions_lists = []
        
        num_model_predictions_values = sorted(list(set(pred_counts.values())))
        
        for num_models in num_model_predictions_values:
            counted_pred_list = []
            for rxn in pred_counts:
                if pred_counts[rxn] == num_models:
                    counted_pred_list.append(rxn)
            
            num_model_predictions_lists.append([num_models, counted_pred_list])
        
        
        for pred_data in num_model_predictions_lists:
            pred_set = pred_set - set(pred_data[1])
            if len(pred_set) == 0:
                break
             
            num_preds_ref = len(pred_set & dev_not_ref)
            num_preds_not_ref = len(pred_set) - num_preds_ref
             
            
            print("{:1} or more models:\t{:5}\t{:5}\t{:.3f}".format(
                pred_data[0] + 1,
                num_preds_ref,
                num_preds_not_ref,
                num_preds_ref/float(len(pred_set))
            ))       
        
        
        ## 
        
        
        
        
        
        
        
        
        
          