from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter, dict_append, dict_count


class Command(BaseCommand):
    
    #help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ From the Combfunc_predictions table infer reactions predictions for Combfunc.
            
        """ 
        
        Combfunc_prediction.objects.all().delete()
        
        
        ## Create dictionaries for inferring reactions from GO terms
        
        print("Creating GO/Reaction dictionaries ...")
        
        distinct_go2rxn = GO_Reaction.objects\
                .values('go_id','reaction__name')\
                .distinct()\
        
        go_count = {}
        rxn_count = {}
        go_2f_rxn_dict = {}
        
        for entry in distinct_go2rxn:
            
            ## Populate GO to/from reaction dictionary
            
            dict_append(go_2f_rxn_dict, entry['go_id'], entry['reaction__name'])
            dict_append(go_2f_rxn_dict, entry['reaction__name'], entry['go_id'])
            
            if entry['go_id'] in go_count:
                go_count[entry['go_id']] += 1
            else:
                go_count[entry['go_id']] = 1
            
            if entry['reaction__name'] in rxn_count:
                rxn_count[entry['reaction__name']] += 1
            else:
                rxn_count[entry['reaction__name']] = 1
                
        
        ## Set cutoffs for including predictions
        
        go_specificity_threshold = 20
        score_threshold = 0.3
        
        
        ## Run through Combfunc results and populate Combfunc_prediction table
        
        print("Inferring Combfunc predictions from results ...")
        
        results = Combfunc_result.objects.all()
        
        counter = loop_counter(len(results))
        
        pred_list = [] 
        
        rxn_predicted_count_dict = {}
        gene_predicted_count_dict = {}
        
        for result in results:
            
            ## Does GO term have reactions associated with it?
            if result.go_term.id in go_2f_rxn_dict:
                
                if result.score >= score_threshold:
                
                    ## Is number of reactions associated with that GO term below the threshold?
                    if go_count[result.go_term.id] <= go_specificity_threshold:
                        
                        ## Add predictions to Combfunc_prediction
                        
                        for name in go_2f_rxn_dict[result.go_term.id]:
                            
#                             if id in rxn_predicted_count_dict:
#                                 rxn_predicted_count_dict[id] += 1
#                             else:
#                                 rxn_predicted_count_dict[id] = 1
                             
                            dict_count(rxn_predicted_count_dict,name)
                            dict_count(gene_predicted_count_dict,result.gene)
                            
                            reaction = Reaction.objects.get(name=name)
                            total_score = result.score / len(go_2f_rxn_dict[result.go_term.id])
                            score = result.score
                            
                            
                            pred = Combfunc_prediction(
                                go = result.go_term,
                                result = result,
                                gene = result.gene,
                                reaction = reaction,
                                total_score=total_score,
                                combfunc_score=score,
                                num_predictions_go = len(go_2f_rxn_dict[result.go_term.id])
                                )
                            
                            pred_list.append(pred)
        
            counter.step()
                 
        counter.stop()
        
        counter = loop_counter(len(pred_list))        
        
        for pred in pred_list:
            
            num_rxn = rxn_predicted_count_dict[pred.reaction.name]
            num_gene = gene_predicted_count_dict[pred.gene]
            
            pred.num_predictions_gene = num_gene
            pred.num_predictions_reaction = num_rxn
#             pred.total_score = pred.total_score / num_rxn 
            
            pred.save()

            counter.step()
                 
        counter.stop()
        print("Number of predictions = %d" % len(pred_list))                           
