from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter


class Command(BaseCommand):
    
    help = 'Convert Eficaz results to predictions.'
        
    def handle(self, *args, **options):
        
        """ 'Convert Eficaz results to predictions.'
            
        """ 
        
        
        ###! For each Eficaz result, get all reactions related to the
        ###! GO term, and add them to the Eficaz_prediction table,
        ###! with appropriate scores.

        
        eficaz_score_cutoff = 0.7
        
        ##! Delete all Eficaz reaction predictions (Eficaz_prediction)
        print "Deleting previous Eficaz predictions ..."
        Eficaz_prediction.objects.all().delete()
        
        num_genes = Gene.objects.all().count()
        
        print 'Inferring Eficaz reaction prediction data ...'
        #Initiate counter
        counter = loop_counter(num_genes)
        
        list_of_predictions = []
        list_preds = []
        num_predictions_gene = {}
        num_predictions_reaction = {}
        
        #  ##! Get highest score from Eficaz_result to normalise the prediction scores.
        #scores = Eficaz_result.objects.all().order_by('-score').values_list('score', flat=True)
        #max_score = scores[0]
        #print("Max score = %d" % max_score)
        
        for gene in Gene.objects.all():
            
            counter.step()
            
            ## Find all Eficaz predictions for that gene
            
            prev_num_predictions = len(list_of_predictions)
            
            num = Eficaz_result.objects.filter(gene=gene).count()
            
            #print("Gene %s - %d" % (gene.gi, num))
            
            ## If at least one prediction above the threshold - for now filter out 3-number ECs
            if Eficaz_result.objects.filter(
                    gene=gene,
                    precision_mean__gte=(eficaz_score_cutoff)
                ).exclude(
                    ec__number__endswith="-"
                ).count() > 0:
                
                
                results = Eficaz_result.objects.filter(
                    gene=gene,
                    precision_mean__gte=(eficaz_score_cutoff))\
                .exclude(ec__number__endswith="-")
                
                
                for result in results:
                
                    ## Find all reactions related to relevant EC number
                    
                    ec = result.ec
                    reactions = Reaction.objects.filter(ec_reaction__ec=ec)
                    num_predictions_ec = reactions.count()
                    
                    ## Append to list of predictions so stats can be calculated
                    for reaction in reactions:
                        
                        list_of_predictions.append((
                            gene,
                            reaction,
                            result,
                            num_predictions_ec,
                            ec
                        ))
                        
                        
                        ## Count number of times reaction appears in predictions
                        if reaction.name in num_predictions_reaction:
                            num_predictions_reaction[reaction.name] += 1
                        else:
                            num_predictions_reaction[reaction.name] = 1
            
            ## Count total number of predictions for gene -> num_predictions_gene
            num_predictions_gene[gene.gi] = len(list_of_predictions) - prev_num_predictions

        counter.stop()
        
        print 'Total number of predictions = %d\n' % len(list_of_predictions)
        
        print "Populating Eficaz prediction table ..."

        counter = loop_counter(len(list_of_predictions))
        
        
        ## Add global stats (for ease of calculations)
        for prediction in list_of_predictions:
            counter.step()
            
            #print prediction
            eficaz_prediction = Eficaz_prediction(
                gene=prediction[0],
                reaction=prediction[1],
                result=prediction[2],
                eficaz_score=prediction[2].precision_mean,
                num_predictions_ec=prediction[3],
                num_predictions_gene = num_predictions_gene[prediction[0].gi],
                num_predictions_reaction = num_predictions_reaction[prediction[1].name],
                total_score=prediction[2].precision_mean,
            )
            
            eficaz_prediction.total_score = eficaz_prediction.eficaz_score/eficaz_prediction.num_predictions_ec
            
            eficaz_prediction.save()
            
        counter.stop()