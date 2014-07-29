from django.core.management.base import NoArgsCommand, CommandError
from annotation.models import GO, Reaction, Gene, Profunc_result, GO_Reaction, Profunc_prediction
#from ffpred.extract_results import *
import sys, os, re, shelve
from myutils.general.utils import loop_counter, dict_count
import matplotlib.pyplot as plt

class Command(NoArgsCommand):
    
    help = 'Steps through the analysis of data from Profunc to infer the metabolic functions of all genes in the BTH genome.'
        
    def handle(self, **options):
        
        found_example = 0
        
        ###! For each Profunc result, get all reactions related to the
        ###! GO term, and add them to the Profunc_prediction table,
        ###! with appropriate scores.
        
        profunc_score_cutoff = 0.05
        go_reaction_limit = 3
        
        ##! Delete all Profunc reaction predictions (Profunc_prediction)
        print "Deleting previous Profunc predictions ..."
        Profunc_prediction.objects.all().delete()
        
        num_genes = Gene.objects.all().count()
        
        print 'Inferring Profunc reaction prediction data ...'      
        
        list_of_predictions = []
        list_preds = []
        num_predictions_gene = {}
        num_predictions_reaction = {}
        
        ## Get highest score from Profunc_result to normalise the prediction scores.
        scores = Profunc_result.objects.all().order_by('-score').values_list('score', flat=True)
        max_score = scores[0]
        print("Max score = %d" % max_score)
        
#         counter = loop_counter(num_genes)
        
        gene_pred_counts = []
        
        for gene in Gene.objects.all():
            
            prev_num_predictions = len(list_of_predictions)
#             counter.step(prev_num_predictions)
            
            
            ## Find all Profunc predictions for that gene
            
            if Profunc_result.objects.filter(
                gene=gene,
                score__gte=(profunc_score_cutoff*max_score)
                ).count() > 0:
                
                results = Profunc_result.objects.filter(
                    gene=gene,
                    score__gte=(profunc_score_cutoff*max_score)
                    )
                
                #if results.count() > 10:
                    
                                
                for result in results:
                
                    ## Find all reactions related to relevant GO term
                    
                    go = result.go_term
                    #print(" - %s" % go)
                        
                    reactions = Reaction.objects.filter(go_reaction__go=go)
                    num_predictions_go = reactions.count()
                    if num_predictions_go <= go_reaction_limit:
                        for reaction in reactions:
                            
                            list_of_predictions.append((
                                gene,
                                reaction,
                                result.score,
                                num_predictions_go,
                                go
                            ))
                            
                            ## Add count to reaction in rxn dictionary
                            dict_count(num_predictions_reaction, reaction.name)
                                        
                        
#                 break

            ## Count total number of predictions for gene -> num_predictions_gene
            num_predictions_gene[gene.gi] = len(list_of_predictions) - prev_num_predictions
#             print gene.gi

#             print("%10d, %d" % (num_predictions_gene[gene.gi],len(results)))

            print("%8s: %4d results, %4d predictions" % (gene.locus_tag,len(results), num_predictions_gene[gene.gi]))
            if num_predictions_gene[gene.gi] > 0:
                gene_pred_counts.append(num_predictions_gene[gene.gi])

#         counter.stop()        
        
#         plt.hist(gene_pred_counts, 100)
#         plt.show()
        
        print 'Total number of predictions = %d\n' % len(list_of_predictions)
        
#         sys.exit(0)
        
        print "Populating Profunc prediction table ..."

        counter=loop_counter(len(list_of_predictions))
        
        ## Add global stats (for ease of calculations)
        for prediction in list_of_predictions:
            
            counter.step()
            
            profunc_score = prediction[2]/float(max_score)
            
            total_score = profunc_score/num_predictions_gene[prediction[0].gi]
            
            #print prediction
            profunc_prediction = Profunc_prediction(
                gene=prediction[0],
                reaction=prediction[1],
                profunc_score=profunc_score,
                num_predictions_go=prediction[3],
                ##! Keyerror - why isn't nu_predictions_gene found?
                num_predictions_gene = num_predictions_gene[prediction[0].gi],
                num_predictions_reaction = num_predictions_reaction[prediction[1].name],
                total_score=total_score,
                go=prediction[4]
            )
            
            #print "%s: %d\t\t%s: %d\n" % (
            #    prediction[0].gi,
            #    num_predictions_gene[prediction[0].gi],
            #    prediction[1].id,
            #    num_predictions_reaction[prediction[1].id]
            #)
            
            profunc_prediction.save()

        counter.stop()
