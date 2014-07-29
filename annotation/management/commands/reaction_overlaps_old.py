from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, F, Q, Avg
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter


class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        ## Cycle through command line arguments
        num_args = 0
        for arg in args:
            num_args += 1
        
        in_reactions = Reaction.objects.filter(source__name="iAH991__P2M_BT__BioCyc__step_3.xml", name="LARGNAT").exclude(name__startswith="MNXR")
                
        find_reaction_overlaps(in_reactions)
        

def find_reaction_overlaps(in_reactions, source = None):
    """
    For a reaction, find and print out all reactions overlapping by more than one metabolite, starting with highest overlap.
    """
    
#     if source is not None:
#         try:
#             in_reaction = Reaction.objects.get(name=in_reaction, source=source)
#         except:
#             print("Reaction not found ...")
#             sys.exit(1)
    
#     counter = loop_counter(in_reactions.count())
    
    for in_reaction in in_reactions:
#         counter.step()
        ### Get list of stoichiometries for reactions sharing two or more metabolites with the reaction
        
        num_mets = in_reaction.stoichiometry_set.count()
        
        in_num_mets = in_reaction.stoichiometry_set.count()
        
        if num_mets > 2:
        
            overlaps_found = False
            equivalent_rxns = True
            
            while not overlaps_found:
                overlap_rxns = Reaction.objects\
                    .filter(stoichiometry__metabolite__in 
                            = Metabolite.objects
                                .filter(stoichiometry__reaction=in_reaction)
                                .distinct())\
                    .annotate(num_mets_overlap=Count('id'))\
                    .distinct()\
                    .annotate(num_mets_total=Count('stoichiometry'))\
                    .filter(num_mets_total=in_num_mets,num_mets_overlap=num_mets)\
                    .exclude(name=in_reaction.name)\
                    .distinct()
                
                
                
                
                num_mets -= 2
                
                if equivalent_rxns:
                    if overlap_rxns.count() > 0:
                        print("Reaction '%s':" % in_reaction.name)
                        print(" - %s" % in_reaction.equation()) 
                        print(" -> Identical reactions:")
                        for rxn in overlap_rxns:
                            print rxn
                            print(" - %s [%d, %s, %s]" % (rxn.equation(), rxn.id, rxn.name, rxn.source))
                    equivalent_rxns = False
                else:
                    overlaps_found = True
#                     if overlap_rxns.count() > 0:
#                         print("\nReaction '%s':" % in_reaction.name)
#                         print(" - %s" % in_reaction.equation())
#                         print(" -> Diff by one metabolite:")
#                         for rxn in overlap_rxns:
#                             print(" - %s [%d, %s, %s]" % (rxn.equation(), rxn.id, rxn.name, rxn.source))
            
#             print "\n" 
#     counter.stop()                   