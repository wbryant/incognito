from django.core.management.base import NoArgsCommand, CommandError
from annotation.models import GO
import sys, re

class Command(NoArgsCommand):
    
    help = 'Imports data to the GO table from the geneontology.org website.'
        
    def handle(self, **options):
        
        GO.objects.all().delete()
        
        f_in = open('/Users/wbryant/work/BTH/data/geneontology/go_mf_terms.tsv', 'r')
        
        num_lines = 0
        for line in f_in:
            num_lines += 1
        f_in.close()
        f_in = open('/Users/wbryant/work/BTH/data/geneontology/go_mf_terms.tsv', 'r')
        
        print 'Populating GO table ...'
        #Initiate counter
        num_tot = num_lines
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()
    
        for line in f_in:
            line = line.strip().split('\t')
            valid_line = False
            if line[0][0:3] == 'GO:':
                valid_line = True
           
            if valid_line:
                go_term = line[0]
                name = line[1]
                
                go = GO(
                    id = go_term,
                    name = name
                )
                
                try:
                    go.save()
                except:
                    print 'GO term not saved successfully: %s' % go_term
                    
            
            #Counter
            num_done += 1
            if ((100 * num_done) / num_tot) > next_progress:
                sys.stdout.write("\r - %d %%" % next_progress)
                sys.stdout.flush()
                next_progress += 1
        
        f_in.close()
        
        #Finish counter
        sys.stdout.write("\r - 100 %\n")
        sys.stdout.flush()
