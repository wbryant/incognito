from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re


class Command(BaseCommand):
    
    help = 'Find and remove all duplicate gene ID / GO term results in Profunc_results table.'
        
    def handle(self, *args, **options):
        
        """ Find and remove all duplicate gene ID / GO term results in Profunc_results table.
            
        """ 
        
        ## Cycle through command line arguments
        num_args = 0
        for arg in args:
            num_args += 1
        
        ### Identify duplicate records and remove them
        
        ## Get all gene ID/GO term duplicate entries
        
        duplicates_list = Profunc_result.objects\
                            .values('gene_id','go_term_id')\
                            .annotate(number=models.Count('pk'))\
                            .filter(number__gt=1) 
        
        ### For each duplicate, find IDs for those duplicates and use all but one of these to eliminate duplicates
        
        
        ## Initiate counter
        num_tot = len(duplicates_list)
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()
        
        
        for dup in duplicates_list:
            
            #if num_done == 5:
            #    break
            
            gene_id = dup['gene_id']
            go_term_id = dup['go_term_id']
            #print("Result: %s - %s" % (gene_id, go_term_id))
            
            ## Get all records with these data
        
            results = Profunc_result.objects.filter(gene_id=gene_id, go_term_id=go_term_id).order_by('-score')
            
            #print type(results)
            #results = list(results)
            
            #for result in results:
            #    print(" - %s, %s, %s" % (result.id, result.go_term_id, result.score))
            
            #print("\n")
            
            results = results[1:]
            for result in results:
                #print(" - %s, %s, %s" % (result.id, result.go_term_id, result.score))
                result.delete()
            
            ## Counter
            num_done += 1
            if ((100 * num_done) / num_tot) > next_progress:
                sys.stdout.write("\r - %d %%" % next_progress)
                sys.stdout.flush()
                next_progress += 1
                
        ## Finish counter
        sys.stdout.write("\r - 100 %\n")
        sys.stdout.flush()
                
                
                