from django.core.management.base import BaseCommand, CommandError
from annotation.models import Model_reaction
from cogzymes.models import Organism, Cog
import sys, os, re
from myutils.general.utils import loop_counter
from django.db.models import Q


class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        ## Cycle through command line arguments
        num_args = 0
        for arg in args:
            num_args += 1
        
        if len(args) <> 1:
            print("Single taxonomy ID required as input ...")
            sys.exit(1)
        else:
            tax_id = args[0]
        
        
        ## Get reactions for taxonomy ID
        
        try:
            dev_organism = Organism.objects.get(taxonomy_id=tax_id)
        except:
            print("Taxonomy ID {} was not found in the eggNOG dataset ...".format(tax_id))
        
        
        dev_cogs = Cog.objects.filter(gene__organism=dev_organism)
        
        ijo_reactions = Model_reaction.objects\
            .filter(source__name='iJO1366')\
            .exclude(~Q(cog_enzymes__cogzymes__in=dev_cogs))
        
        
        
        
        
        