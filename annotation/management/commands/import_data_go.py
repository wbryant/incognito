from django.core.management.base import NoArgsCommand, CommandError
from annotation.models import GO
import sys, re, os
from goatools import obo_parser

class Command(NoArgsCommand):
    
    help = 'Imports data to the GO table from latest OBO format file from the geneontology.org website.'
    
    def handle(self, **options):
        
        #GO.objects.all().delete()
        
        p = obo_parser.GODag('/Users/wbryant/work/BTH/data/geneontology/gene_ontology.1_2.obo')
        
        print 'Populating GO table ...'
        #Initiate counter
        num_tot = len(p)
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()
    
        for term in p:
            if p[term].namespace == 'molecular_function':
                go = GO(
                    id = p[term].id,
                    name = p[term].name
                )
                
                try:
                    go.save()
                except:
                    print 'GO term not saved successfully: %s' % go_term
            #else:
            #    print p[term].namespace
            
            #Counter
            num_done += 1
            if ((100 * num_done) / num_tot) > next_progress:
                sys.stdout.write("\r - %d %%" % next_progress)
                sys.stdout.flush()
                next_progress += 1
        
        #Finish counter
        sys.stdout.write("\r - 100 %\n")
        sys.stdout.flush()
