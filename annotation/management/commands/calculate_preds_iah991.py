from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re


class Command(BaseCommand):
    
    help = 'Take imported information in DB and create predictions.' 
        
    def handle(self, *args, **options):
        
        """ Data imported from iAH991 is put in 
        Iah991_prediction for easy comparison with 
        other predictions.    
        """ 
        
        Iah991_prediction.objects.all().delete()
        
        ###! Propagate through Gene/Enzyme/Reaction relationship for iAH991 reactions and add them as predictions 
        
        enzymes = Enzyme.objects.filter(source="iAH991").exclude(name='GAP').prefetch_related()
        
        print("Preparing results from model ...")
        
        ## Initiate counter
        num_tot = enzymes.count()
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()
        
        reaction_count_dict = {}
        gene_count_dict = {}
        
        pred_list = []
        
        for enzyme in enzymes:
            
            ## Retrieve relevant objects from enzyme
            genes = enzyme.genes.all().distinct()
            num_genes = genes.count()
        
            reactions = enzyme.reaction_set.all().distinct()
            num_reactions = reactions.count()
            
            if (num_genes > 0) & (num_reactions > 0):
                
                for reaction in reactions:
                    
                    if reaction in reaction_count_dict:
                        reaction_count_dict[reaction] += num_genes
                    else:
                        reaction_count_dict[reaction] = num_genes
                    
                    for gene in genes:
                        
                        if gene in gene_count_dict:
                            gene_count_dict[gene] += 1
                        else:
                            gene_count_dict[gene] = 1
                    
                        
                        iah991_prediction = Iah991_prediction(
                            gene=gene,
                            reaction=reaction
                        )
                        
                        pred_list.append(iah991_prediction)
        
            ## Counter
            num_done += 1
            if ((100 * num_done) / num_tot) > next_progress:
                sys.stdout.write("\r - %d %%" % next_progress)
                sys.stdout.flush()
                next_progress += 1
                
        ## Finish counter
        sys.stdout.write("\r - 100 %\n")
        sys.stdout.flush()
        
        print("Number of predictions = {}".format(len(pred_list)))
         
        print("Populating Iah991_prediction table ...")        
                
        ## Initiate counter
        num_tot = len(pred_list)
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()
        
        for pred in pred_list:
            pred.num_predictions_gene = gene_count_dict[pred.gene]
            pred.num_predictions_reaction = reaction_count_dict[pred.reaction]
            
            #print("%s - %s: %d, %d" % (pred.gene, pred.reaction, pred.num_predictions_gene, pred.num_predictions_reaction))
            pred.save()
        
            ## Counter
            num_done += 1
            if ((100 * num_done) / num_tot) > next_progress:
                sys.stdout.write("\r - %d %%" % next_progress)
                sys.stdout.flush()
                next_progress += 1
                
        ## Finish counter
        sys.stdout.write("\r - 100 %\n")
        sys.stdout.flush()
      