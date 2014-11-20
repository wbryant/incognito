from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q, Count
from annotation.models import *
from cogzymes.models import *
from myutils.general.utils import dict_append, preview_dict, loop_counter
from myutils.stats import proportions
import sys, os, re
from collections import Counter

from itertools import groupby, product
from operator import itemgetter
from myutils.general.mnxref_reac_extract import Rxn_ids

def evaluate_predictions_by_number_of_cogs_in_cogzyme(dev_model, ref_models, ref_rxns):
    """
    Look at the number of COGs in the largest COGzyme predicting each predicted reaction
    """
    
    ## Create list of tuples of (reaction, num_cogs_in_pred_cogzyme)
    
    num_cogs_tuples = Cogzyme.objects\
        .filter(
            reaction_pred__dev_model=dev_model,
            reaction_pred__reaction__db_reaction__isnull = False
        )\
        .annotate(num_cogs=Count('cogs'))\
        .values_list('reaction_pred__reaction__db_reaction__name','num_cogs')
    
    num_cogs_tuples = sorted(num_cogs_tuples, key=itemgetter(0))
    num_cogs_tuples = sorted(num_cogs_tuples, key=itemgetter(1), reverse=True)
    rxn_cogcount_dict = {}
    for item in num_cogs_tuples:
        if item[0] not in rxn_cogcount_dict:
            rxn_cogcount_dict[item[0]] = item[1] 
    
    cogcount_rxn_dict = {}
    for rxn in rxn_cogcount_dict:
        count = rxn_cogcount_dict[rxn]
        dict_append(cogcount_rxn_dict, count, rxn)
    
    cogcount_rxn_list = []
    for count in cogcount_rxn_dict:
        rxn_list = cogcount_rxn_dict[count]
        cogcount_rxn_list.append([count,set(rxn_list)])
    
    cogcount_rxn_list = sorted(cogcount_rxn_list, key=itemgetter(0), reverse=True)
    
    pred_rxns_cumulative = set()
    for count in cogcount_rxn_list:
        description = "Number of COGs in COGzyme >= {}".format(count[0])
        pred_rxns_cumulative = pred_rxns_cumulative | count[1] 
        evaluate_prediction_quality(pred_rxns_cumulative, ref_rxns, description)
    
    
    
def evaluate_predictions_by_connectivity(dev_model, ref_models, ref_rxns):
    """
    Look  at the proportion of metabolites in each predicted reaction 
    for the dev_model, from the ref_models specified
    """
    
    dbrxn_pred_list = Reaction.objects.filter(
        model_reaction__reaction_pred__dev_model=dev_model,
        model_reaction__reaction_pred__ref_model__in=ref_models
    ).distinct()
    
    print("Number of predictions = {}".format(dbrxn_pred_list.count()))
    
#     counter = loop_counter(dbrxn_pred_list.count(), "Calculating reaction connectivities to current model")
    
    num_bins = 10
    bin_size = 1/float(num_bins)
    pred_met_mapped_bins = []
    for i in range(0,num_bins+1):
        bin_upper_bound = i * bin_size
        pred_met_mapped_bins.append([bin_upper_bound,[]])
    
    
    for dbrxn in dbrxn_pred_list:
        num_mets = dbrxn.stoichiometry_set.all().count()
        num_mets_mapped = dbrxn.stoichiometry_set.filter(metabolite__model_metabolite__source=dev_model).distinct().count()
        
        mapped_proportion = float(num_mets_mapped)/num_mets
        
        for bin in pred_met_mapped_bins:
            if mapped_proportion >= bin[0]:
                bin[1].append(dbrxn.name)
#                 break
    
    for bin in pred_met_mapped_bins:
        dev_rxns = set(bin[1])
        description = "Proportion of mapped mets >={}".format(bin[0])
        evaluate_prediction_quality(dev_rxns, ref_rxns, description)
        
    
# def count_first_value(Model, filter_kwargs, values_strings):
#     """
#     Do a filter on Model, returning counts (a Counter object) for the first 
#     value in values_strings of the distinct sets of all values returned by the 
#     values in values_strings.
#     
#     """
#     
#     distinct_counts = Counter(zip(*list(
#         Reaction_pred.objects
#         .filter(**filter_kwargs)
#         .values_list(*values_strings)
#         .distinct()
#     ))[0])
#     
#     return distinct_counts

def evaluate_prediction_quality(pred_set, ref_set, description = "Quality scores"):
    
    if ((not pred_set) or (len(pred_set) == 0)):
        num_preds_ref = 0
        num_preds_not_ref = 0
        proportion = 0
    else:
        num_preds_ref = len(pred_set & ref_set)
        num_preds_not_ref = len(pred_set) - num_preds_ref
        proportion = num_preds_ref/float(len(pred_set))
    
    print("{:32}:\t{:5}\t{:5}\t{:.3f}".format(
        description,
        num_preds_ref,
        num_preds_not_ref,
        proportion
    )) 

def evaluate_prediction_quality_diff(pred_set1, pred_set2, ref_set, significance_level = 0.05, description="pred_set1 against pred_set2"):
    """Evaluate whether there is a statistically significant difference between the qualities of the two prediction sets.
    
    tp - true positive
    fp - false positive
    """
    
    tp1 = len(pred_set1 & ref_set)
    fp1 = len(pred_set1) - tp1
    tp2 = len(pred_set2 & ref_set)
    fp2 = len(pred_set1) - tp2
    
    
    z_score, p_value = proportions.get_z_score(tp1, fp1, tp2, fp2, one_tail=False)
    
    print("\n{}:".format(description))
    
    if p_value <= significance_level:
        if z_score > 0:
            result = ", pred_set1 is higher quality than pred_set2"
        else:
            result = ", pred_set2 is higher quality than pred_set1"
        not_or_empty = ""
    else:
        not_or_empty = "not "

    print("\t-> Difference is {}significant (at p = {}){}.".format(not_or_empty, significance_level, result))
    

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
        
        evaluate_predictions_by_number_of_cogs_in_cogzyme(dev_model, ref_models, ref_rxns)
        
        evaluate_predictions_by_connectivity(dev_model, ref_models, ref_rxns)
        
        ## Get all predicted additional reactions, along with number of models predicting those reactions
         
        pred_counts = Counter(zip(*list(
            Reaction_pred.objects
            .filter(dev_model=dev_model, status='add')
            .values_list('reaction__db_reaction__name','ref_model__name')
            .distinct()
        ))[0]) 
         
        pred_set_all = set(pred_counts.keys())
         
         
        evaluate_prediction_quality(pred_set_all, ref_not_dev, "\nAll predictions")
        
         
        ## Look at different numbers of predictions
         
        num_model_predictions_lists = []
         
        num_model_predictions_values = sorted(list(set(pred_counts.values())))
         
        for num_models in num_model_predictions_values:
            counted_pred_list = []
            for rxn in pred_counts:
                if pred_counts[rxn] == num_models:
                    counted_pred_list.append(rxn)
             
            num_model_predictions_lists.append([num_models, counted_pred_list])
         
        pred_set_numpreds = pred_set_all
         
        for pred_data in num_model_predictions_lists:
            pred_set_numpreds = pred_set_numpreds - set(pred_data[1])
            if len(pred_set_numpreds) == 0:
                break
             
            description = "{:1} or more models".format(pred_data[0] + 1)
            evaluate_prediction_quality(pred_set_numpreds, ref_not_dev, description)       
 
         
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
          
        description = "With candidate operons"
        evaluate_prediction_quality(pred_set, ref_not_dev, description)
               
          
        ## p_wo_co
        pred_set = p_wo_co
  
        description = "No candidate operons"
        evaluate_prediction_quality(pred_set, ref_not_dev, description)                    
                 
                 
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
         
        description = "\nAll predictions"
        evaluate_prediction_quality(pred_set, dev_not_ref, description)
         
 
 
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
              
            description = "{:1} or more models".format(pred_data[0] + 1)
            evaluate_prediction_quality(pred_set, dev_not_ref, description)
         
     
        ## Model, Suspect and Hidden COGzymes - any difference?
        ## -> Prediction type precalculated for all predictions, so should be simple to implement
         
        ## Model
        pred_set_model = set(
                Reaction_pred.objects
                .filter(dev_model=dev_model, type = 'mod', status='add')
                .values_list('reaction__db_reaction__name', flat=True)
                .distinct()
            )
         
        description = "\nCOGzymes already in model"
        evaluate_prediction_quality(pred_set_model, ref_not_dev, description)
         
        ## Suspect
        pred_set_suspect = set(
                Reaction_pred.objects
                .filter(dev_model=dev_model, type = 'sus', status='add')
                .values_list('reaction__db_reaction__name', flat=True)
                .distinct()
            )
         
        description = "COGzyme components already in model"
        evaluate_prediction_quality(pred_set_suspect, ref_not_dev, description)
         
        ## Hidden
        pred_set_hidden = set(
                Reaction_pred.objects
                .filter(dev_model=dev_model, type = 'hid', status='add')
                .values_list('reaction__db_reaction__name', flat=True)
                .distinct()
            )
         
        description = "COGzyme components not all in model"
        evaluate_prediction_quality(pred_set_hidden, ref_not_dev, description)
         
        pred_set_non_model = pred_set_suspect | pred_set_hidden
         
        evaluate_prediction_quality(pred_set_non_model, ref_not_dev)
         
        description = "Testing model COGzyme against non-model COGzyme predictions"
        evaluate_prediction_quality_diff(pred_set_model, pred_set_non_model, ref_not_dev, description=description)
         
         
        ## NUMBER OF REACTIONS FOR EACH COGZYME
        print("\nPredictions according to COGzyme specificity:")
         
        ## Get all cogzymes for all predictions
         
        all_cogzymes = Cogzyme.objects.filter(
            reaction_pred__dev_model=dev_model)\
            .distinct()
         
        ## For each of these cogzymes find how many db_reactions are catalysed by them
         
        dbrxn_count_for_cogzymes = Counter(zip(*list(
            Enzyme.objects\
                .filter(cogzyme__in=all_cogzymes)\
                .values_list('cogzyme__name','reactions__db_reaction__name')\
                .distinct()
        ))[0])
         
        ## For each prediction with a db_reaction, get the reaction with the cogzyme reaction count
        dbrxn_cogzyme_pairs = Reaction_pred.objects\
            .filter(
                dev_model=dev_model,
                reaction__db_reaction__isnull = False,
                status = 'add'
            )\
            .values_list(
                'reaction__db_reaction__name',
                'cogzyme__name'
            )
         
        ## Find counts of reactions for cogzymes for each prediction
        dbrxn_czcount_pairs = []
        for entry in dbrxn_cogzyme_pairs:
            name = entry[0]
            cz_count = dbrxn_count_for_cogzymes[entry[1]]
            dbrxn_czcount_pairs.append([name, cz_count])
        dbrxn_czcount_pairs.sort()
         
        ## Remove duplicates by grouping
        ndup_dbrxn_czcount_pairs = list(dbrxn_czcount_pairs for dbrxn_czcount_pairs,_ in groupby(dbrxn_czcount_pairs))
        ndup_dbrxn_czcount_pairs.sort(key=itemgetter(1))
         
        ## Separate predicted reactions by cogzyme reaction count (czcount)
        for num_rxns, pairs in groupby(ndup_dbrxn_czcount_pairs, itemgetter(1)):
            description = ("{} Reactions for COGzyme".format(num_rxns))
            pred_list_czcount = []
            for pair in pairs:
                pred_list_czcount.append(pair[0])
            pred_set_czcount = set(pred_list_czcount)
            evaluate_prediction_quality(pred_set_czcount, ref_not_dev, description)
         
        ## Separate predicted reactions by cutoff value
        cutoff = 20
         
        for cutoff in range(1,10):
            pred_list_czcount_lte = []
            pred_list_czcount_gt = []
            for num_rxns, pairs in groupby(ndup_dbrxn_czcount_pairs, itemgetter(1)):
                pred_list_czcount = []
                for pair in pairs:
                    pred_list_czcount.append(pair[0])
                if num_rxns <= cutoff:
                    pred_list_czcount_lte.extend(pred_list_czcount)
                else:
                    pred_list_czcount_gt.extend(pred_list_czcount)
             
            pred_set_czcount_lte = set(pred_list_czcount_lte)
            pred_set_czcount_gt = set(pred_list_czcount_gt)
             
            description = ("LTE {} Reactions for COGzyme".format(cutoff))
            evaluate_prediction_quality(pred_set_czcount_lte, ref_not_dev, description)
             
            description = ("GT {} Reactions for COGzyme".format(cutoff))
            evaluate_prediction_quality(pred_set_czcount_gt, ref_not_dev, description)
         
        