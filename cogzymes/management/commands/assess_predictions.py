from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q, Count
from annotation.models import *
from cogzymes.models import *
from myutils.general.utils import dict_append, preview_dict
import sys, os, re

from itertools import groupby, product
from operator import itemgetter

def bsu_correction(bsu_num):
    """Many BSU gene names have an excess 0 at the end, making consecutive inferences difficult.
    Remove this zero.  This is not perfect as a few genes have a non-zero last digit - ignore these for now.
    """
    
    bsu_str = str(bsu_num)
    
    if bsu_str[-1] == '0':
        bsu_num = int(bsu_str[:-1])
    
    return bsu_num
     

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
        
#         while num_reactions > 0:
#             
#             num_predictions += 1
#             
#             try:
#                 preds = zip(*list(Reaction.objects\
#                     .filter(
#                         model_reaction__reaction_pred__dev_model=dev_model,
#                         model_reaction__reaction_pred__status='add'
#                     )\
#                     .values('model_reaction__reaction_pred__ref_model__name')\
#                     .annotate(num_preds=Count('model_reaction__reaction_pred__ref_model__name'))\
#                     .order_by()\
#                     .filter(num_preds__eq=num_predictions)\
#                     .values_list('name', 'num_preds')))[0]
#             except:
#                 preds = []
#             
#             num_reactions = len(preds)
#             
#             if num_reactions > 0:
#                 num_model_predictions_lists.append(preds)
#             
#             
#         """For each number of models predicting each reaction, for the reaction list calculate:
#         
#         1.    How many are in the reference model for the organism?
#         2.    How many are not in the reference model for the organism?"""
#         
#         for idx, prediction_list in enumerate(num_model_predictions_lists):
#             num_models_predicting = idx + 1
#             pred_set = set(prediction_list)
#             
#             num_preds_ref = len(pred_set & ref_not_dev)
#             num_preds_not_ref = len(pred_set) - num_preds_ref
#             
#             print("{:1} models:\t{:5}\t{:5}\t{}".format(
#                 num_models_predicting,
#                 num_preds_ref,
#                 num_preds_not_ref,
#                 num_preds_ref/float(len(pred_set))
#             ))
        
        ## Look at each prediction to see whether enzymes could be made up from adjacent genes in dev genome
        ##  - Assumes sequential numbering of all genes at end of locus tag
        
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
                
#                 preview_dict(locus_num_tag_dict)
#                 preview_dict(locus_cog_dict)
                
#                 print("Number of non divisible locus numbers = {}".format(locus_nums_not_mult10))
                
                locus_nums_sorted = sorted(list(set(locus_num_list)))
#                 print("\nLocus_nums_sorted:")
#                 print locus_nums_sorted
                
                ## COG set for COGzyme
                cogzyme_cog_set = set(prediction.cogzyme.name.split(","))
#                 print("\ncogzyme_cog_set:")
#                 print cogzyme_cog_set
                
                
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
                        
                        if prediction.reaction.db_reaction.name in ref_not_dev:
                            print("\nSubset found for prediction {}:".format(prediction.pk))
                         
                            print("cogzyme_cog_set for genes:")
                            print cogzyme_cog_set
    
                            print("gene_set:")
                            print gene_set
                            for locus in gene_set:
                                print locus, locus_cog_dict[locus]
                            print("--> correct prediction")
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
        
        print("\nWith candidate operons:\t{:5}\t{:5}\t{}".format(
            num_preds_ref,
            num_preds_not_ref,
            num_preds_ref/float(len(pred_set))
        ))                
        
        ## p_wo_co
        pred_set = p_wo_co
        num_preds_ref = len(pred_set & ref_not_dev)
        num_preds_not_ref = len(pred_set) - num_preds_ref
        
        print("Without candidate operons:\t{:5}\t{:5}\t{}".format(
            num_preds_ref,
            num_preds_not_ref,
            num_preds_ref/float(len(pred_set))
        ))                
                