from django.core.management.base import NoArgsCommand, CommandError
from annotation.models import GO, Reaction, Gene, Eficaz_result, GO_Reaction, Eficaz_prediction
#from ffpred.extract_results import *
import sys, os, re, shelve

class Command(NoArgsCommand):
    
    help = 'Steps through the analysis of data from Eficaz to infer the metabolic functions of all genes in the BTH genome.'
        
    def handle(self, **options):
        
        found_example = 0
        
        ###! For each Eficaz result, get all reactions related to the
        ###! EC number, and add them to the Eficaz_prediction table,
        ###! with appropriate scores.
        
        eficaz_score_cutoff = 0.01
        
        ##! Delete all Eficaz reaction predictions (Eficaz_prediction)
        print "Deleting previous Eficaz predictions ..."
        Eficaz_prediction.objects.all().delete()
        
        num_genes = Gene.objects.all().count()
        
        print 'Inferring Eficaz reaction prediction data ...'
        #Initiate counter
        num_tot = num_genes
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()        
        
        list_of_predictions = []
        list_preds = []
        num_predictions_gene = {}
        num_predictions_reaction = {}
        
        
        for gene in Gene.objects.all():
            
            ## Find all Eficaz predictions for that gene
            
            prev_num_predictions = len(list_of_predictions)
            
            num = Eficaz_result.objects.filter(gene=gene).count()
            
            #print("Gene %s - %d" % (gene.gi, num))
            
            if Eficaz_result.objects.filter(
                gene=gene,
                precision_mean__gte=(eficaz_score_cutoff)
                ).count() > 0:
                
            #    print "Gene result found ..."
                
                results = Eficaz_result.objects.filter(
                    gene=gene,
                    precision_mean__gte=(eficaz_score_cutoff)
                    )
                
                #print("Number of results for this gene = %d" % Eficaz_result.objects.filter(
                #    gene=gene,
                #    precision_mean__gte=(eficaz_score_cutoff)
                #    ).count())
                
                for result in results:
                
                    ## Find all reactions related to relevant GO term
                    
                    ec = result.ec
                    #print ec
                    reactions = Reaction.objects.filter(ec_reaction__ec=ec)
                    num_predictions_ec = reactions.count()
                    
                    for reaction in reactions:
                        
                        #print(" - %s" % reaction.mnxref_id)
                        
                        #prediction = FFPred_prediction(
                        #    gene=gene,
                        #    reaction=reaction,
                        #    ffpred_score=result.score,
                        #    num_predictions_go=num_predictions_go,
                        #    total_score=result.score
                        #)
                        
                        list_of_predictions.append((
                            gene,
                            reaction,
                            result.precision_mean,
                            num_predictions_ec,
                            ec,
                            result
                        ))
                        
                        #if reaction.mnxref_id == "MNXR337":
                        #    print "Reaction found: %s - %s" % (gene.gi, go.id)
                        
                        if reaction.name in num_predictions_reaction:
                            num_predictions_reaction[reaction.name] += 1
                            #if reaction.mnxref_id == "MNXR337":
                            #    print "Reaction found %d (%d) times ..." % (num_predictions_reaction[reaction.mnxref_id], num_predictions_reaction["MNXR337"])
                            #print num_predictions_reaction[reaction.mnxref_id]
                        else:
                            num_predictions_reaction[reaction.name] = 1
                        
                        #list_preds.append(prediction)
                #break
            ## Count total number of predictions for gene -> num_predictions_gene
            num_predictions_gene[gene.gi] = len(list_of_predictions) - prev_num_predictions
            #print("Gene GI %s, added to num_predictions_gene" % gene.gi)
            #print num_predictions_gene[gene.gi]
            
            ##? Do any predictions predict the same reactions?

            ##Counter
            #num_done += 1
            #if ((100 * num_done) / num_tot) > next_progress:
            #    sys.stdout.write("\r - %d %%" % next_progress)
            #    sys.stdout.flush()
            #    next_progress += 1
                
        #Finish counter
        sys.stdout.write("\r - 100 %\n")
        sys.stdout.flush()
        
        print 'Total number of predictions = %d\n' % len(list_of_predictions)
        
        print "Populating Eficaz prediction table ..."

        #Initiate counter
        num_tot = len(list_of_predictions)
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()  
        
        ## Add global stats (for ease of calculations)
        for prediction in list_of_predictions:
            #print prediction
            eficaz_prediction = Eficaz_prediction(
                gene=prediction[0],
                reaction=prediction[1],
                eficaz_score=prediction[2],
                num_predictions_ec=prediction[3],
                ##! Keyerror - why isn't num_predictions_gene found?
                num_predictions_gene = num_predictions_gene[prediction[0].gi],
                num_predictions_reaction = num_predictions_reaction[prediction[1].id],
                total_score=prediction[2],
                result = prediction[5]
                #ec=prediction[4]
            )
            
            #print "%s: %d\t\t%s: %d\n" % (
            #    prediction[0].gi,
            #    num_predictions_gene[prediction[0].gi],
            #    prediction[1].mnxref_id,
            #    num_predictions_reaction[prediction[1].mnxref_id]
            #)
            
            eficaz_prediction.save()

            #Counter
            num_done += 1
            if ((100 * num_done) / num_tot) > next_progress:
                sys.stdout.write("\r - %d %%" % next_progress)
                sys.stdout.flush()
                next_progress += 1
                
        #Finish counter
        sys.stdout.write("\r - 100 %\n")
        sys.stdout.flush()


def get_locus_tag(eficaz_result):
    
    return eficaz_result.gene.locus_tag


def gene2go_ffpred(gene):
    """Input gene ID and output GO terms inferred by FFPred."""
    
    gos = GO.objects.filter()