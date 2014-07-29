from django.core.management.base import BaseCommand
from django.db.models import Count, Avg, F
from annotation.models import Eficaz_prediction
import sys


###! Create pseudo-ROC curve?





class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        ## Cycle through command line arguments
        num_args = 0
        for arg in args:
            num_args += 1
        
        
        ## Initiate counter
        num_tot = len(input_files)
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()
        
        
            ## Counter
            num_done += 1
            if ((100 * num_done) / num_tot) > next_progress:
                sys.stdout.write("\r - %d %%" % next_progress)
                sys.stdout.flush()
                next_progress += 1
                
        ## Finish counter
        sys.stdout.write("\r - 100 %\n")
        sys.stdout.flush()
                
                
                