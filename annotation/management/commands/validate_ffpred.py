from django.core.management.base import NoArgsCommand, CommandError
from annotation.models import Gene,  Enzyme, Catalyst, FFPred_prediction, Reaction
#from ffpred.extract_results import *
import sys, os, re, shelve

class Command(NoArgsCommand):
    
    help = 'Validation for the FFPred predictions in FFPred_prediction.'
        
    def handle(self, **options):
        
        ###! Get Gene-to-Reaction results from iAH991 - use a cutoff of confidence >= 0.5
        
        genes = Gene.objects.all()
        
        num_found = 0
        
        for gene in genes:
            
            ## Find all reactions catalysed by enzymes containing the product of this gene
            
            reactions = Reaction.objects.filter(catalyst__enzyme__genes=gene, catalyst__evidence__source="iAH991")
            
            for reaction in reactions:
                
                ## Does this gene/reaction pair exist in the FFPred predictions?
                
                num_predictions = FFPred_prediction.objects.filter(reaction=reaction, gene=gene).count()
                
                if num_predictions > 0:
                    num_found += 1
                    print "Gene %s, reaction %s - %d" % (gene.locus_tag, reaction.name, num_predictions)
                    predictions = FFPred_prediction.objects.filter(reaction=reaction, gene=gene)
                    for p in predictions:
                        print "\t%s\t%s\t%s\t%s\t%s" % (p.go.id, p.ffpred_score, p.num_predictions_gene, p.num_predictions_reaction, p.num_predictions_go)
            
        
        print num_found
        
        ###! See whether these are present in the FFPred predictions
        ###!    -> if there are multiple genes for each reaction, how do the prediction scores
        ###!    relate to which is (are) the correct gene(s)
        
        