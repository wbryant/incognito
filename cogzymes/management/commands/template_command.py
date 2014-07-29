from django.core.management.base import NoArgsCommand, CommandError
from cogzymes.models import *
from myutils.general.gene_parser import gene_parser
import sys, re

class Command(NoArgsCommand):
    
    help = ""
        
    def handle(self, **options):
        
        ##! Delete old data from tables
        #Example - Catalyst.objects.filter(evidence__source='iAH991').delete()
        
        ##! Open data files
        
        filename = ""
        f_in = open(filename, 'r')
        
        num_lines = 0
        for line in f_in:
            num_lines += 1
        f_in.close()
        
        f_in = open(filename, 'r')
        
        
        print 'Populating iAH991, Enzyme and Catalyst table ...'
        #Initiate counter
        num_tot = num_lines
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()
        
        
        for line in f_in:
            ##! Import data from file
            
            
            # EXAMPLE record creaction
#             enzyme = Enzyme(
#                 name = enzyme_name,
#                 source = source
#             )
#             enzyme.save()

                    
            #Counter
            num_done += 1
            if ((100 * num_done) / num_tot) > next_progress:
                sys.stdout.write("\r - %d %%" % next_progress)
                sys.stdout.flush()
                next_progress += 1
        
        #Finish counter
        sys.stdout.write("\r - 100 %\n")
        sys.stdout.flush()
        
        f_in.close()
