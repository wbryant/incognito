from django.core.management.base import NoArgsCommand, CommandError
from annotation.models import GO, Catalyst, Enzyme, Gene, MTG_cog_result, Reaction
#from ffpred.extract_results import *
import sys, os, re, shelve

class Command(NoArgsCommand):
    
    help = 'Looks for gap-filling candidates from MTG data for iAH991 gaps.'
        
    def handle(self, **options):
        
        ## Find iAH991 gaps
        
        gaps = Reaction.objects.filter(enzymes__name='GAP', catalyst__evidence__source='iAH991').distinct()
        
        
        # Get list of SEED IDs
        
        seed_rxn_list = []
        for gap in gaps:
            ids = gap.seed_id.split(',')
            for id in ids:
                if id[0:3] == 'rxn':
                    seed_rxn_list.append(id)
        
        
        seed_rxn_list = list(set(seed_rxn_list))
        
        
        # Find cog IDs
        
        for seed_rxn in seed_rxn_list:
            
             
            if MTG_cog_result.objects.filter(seed_id=seed_rxn).count() > 0:
            
                print '\nReaction: %s' % seed_rxn
                print ' - %s' % Reaction.objects.filter(seed_id__contains=seed_rxn).values_list('metacyc_id',flat=True)[0]
                
                cog_results = MTG_cog_result.objects.filter(seed_id=seed_rxn).order_by('p_value').values_list('cog_id', 'p_value')
                
                #print cog_results
                
                pval_min = cog_results[0][1]
                
                for cog in cog_results:
                    
                    #Find the relevant genes
                    cog_id = cog[0]
                    score = pval_min/cog[1]
                     

                    if score > 0.01:
                        
                        print '\t - %s\t%s' % (cog_id, score)
                        genes = Gene.objects.filter(cog_id=cog_id).distinct()
                        
                        for gene in genes:    
                            print '\t\t - %s\t%s' % (gene, gene.name)
                            continue
                    else:
                        break
                    
                    
                    #Find if they already have enzymes
                    
                    
                    #If they don't have enzymes, add them
                    
                    
                    #Link the enzymes to the reactions
                    
                    
                    #Report the results in some way.
        
        
    
