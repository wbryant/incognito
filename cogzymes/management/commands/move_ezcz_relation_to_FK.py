from django.core.management.base import BaseCommand, CommandError
from cogzymes.models import Enzyme, Cogzyme
from myutils.general.utils import loop_counter
import sys, os, re
import cogzymes


class Command(BaseCommand):
    
    help = 'Migrate m2m relation between Cogzyme and Enzyme to FK relationship, since each enzyme only has 1 cogzyme'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        ## Cycle through command line arguments
        num_args = 0
        for arg in args:
            num_args += 1
        
        num_enzymes = Enzyme.objects.all().count()
        
        counter = loop_counter(num_enzymes, 'Switching enzyme relations from m2m to FK:')
        
        ## For each enzyme, get the set of cogzyme relations (should only be 1)
        for enzyme in Enzyme.objects.all():
            counter.step()
            
            cogzymes = enzyme.cogzyme_set.all()
            if cogzymes.count() > 1:
                print("")
                print enzyme
                for cogzyme in cogzymes:
                    print cogzyme
                continue
            elif cogzymes.count() == 0:
                continue
            else:
                cogzyme = cogzymes[0]
        
            ## add new relation to that enzyme in enzyme__cogzyme
        
            enzyme.new_cogzyme = cogzyme
            enzyme.save()
        
        counter.stop()
                
                
                