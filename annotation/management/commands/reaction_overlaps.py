from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, F, Q, Avg
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter


class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ 
        COMMAND DESCRIPTION    
        """ 
        
        
        in_reactions = Reaction.objects.filter(source__name="iAH991__P2M_BT__BioCyc__step_3.xml").exclude(name__startswith="MNXR")
                
        mnx2model_rxns = find_reaction_overlaps(in_reactions)
        
        rxn_list = Reaction.objects.filter(eficaz_prediction__total_score__gte=0.5).exclude(metabolic_model__source="iAH991__P2M_BT__BioCyc__step_3.xml").distinct()
        
        check_pred_reactions(rxn_list, mnx2model_rxns)
        

def check_pred_reactions(rxn_list, mnx2model_rxns):
    
    print("")
    for rxn in rxn_list:
        if rxn in mnx2model_rxns:
            print("Reaction '%s' already in model under ID '%s'" % (rxn.name, mnx2model_rxns[rxn]))
        else:
            print("Reaction '%s' not yet in model ..." % rxn.name)
        

def find_reaction_overlaps(in_reactions, source = None):
    """
    For a reaction, find and print out all reactions overlapping by more than one metabolite, starting with highest overlap.
    """
    
    
#     counter = loop_counter(in_reactions.count())
    
    ## Create dictionary of identical reactions (ignoring those in multiple compartments)
    
    mnx_to_bth_reactions = {}
    
    
    for in_reaction in in_reactions:
#         counter.step()
        ### Get list of stoichiometries for reactions sharing two or more metabolites with the reaction
        
        num_mets = in_reaction.stoichiometry_set.count()
        in_reaction_subs = set([])
        in_reaction_prods = set([])
        rxn_compartments = set([])
        for sto in in_reaction.stoichiometry_set.all():
            if sto.stoichiometry < 0:
                in_reaction_subs.add(sto.metabolite.name)
            elif sto.stoichiometry > 0:
                in_reaction_prods.add(sto.metabolite.name)
            try:
                rxn_compartments.add(sto.compartment.id)
            except:
                rxn_compartments.add('unk')
        
        if (num_mets > 2) & (len(rxn_compartments) == 1):
            
            ## Find all reactions with overlapping metabolites
            
            overlap_rxns = Reaction.objects.filter(stoichiometry__metabolite__in 
                                                    = Metabolite.objects.filter(stoichiometry__reaction=in_reaction)
                                                                                    .distinct())\
                                                .annotate(num_mets_overlap=Count('id'))\
                                                .filter(num_mets_overlap=num_mets)\
                                                .exclude(name=in_reaction.name, source=in_reaction.source)
            
            identical_rxns = []
            
            for rxn in overlap_rxns:
                if rxn.stoichiometry_set.count() == num_mets:
                    ## Check that reactions are EXACTLY the same in terms of metabolites
                    rxn_subs = set([])
                    rxn_prods = set([])
                    rxn_compartments = set([])
                    for sto in rxn.stoichiometry_set.all():
                        if sto.stoichiometry < 0:
                            rxn_subs.add(sto.metabolite.name)
                        elif sto.stoichiometry > 0:
                            rxn_prods.add(sto.metabolite.name)
                        try:
                            rxn_compartments.add(sto.compartment.id)
                        except:
                            rxn_compartments.add('unk')
                    
                    ## If reaction takes place in a single compartment
                    if len(rxn_compartments) == 1:
                        ## If half-equations match
                        if (((rxn_subs==in_reaction_subs) & (rxn_prods==in_reaction_prods)) or ((rxn_subs==in_reaction_prods) & (rxn_prods==in_reaction_subs))):
                            ## If the source is the MetaNetX database
                            if rxn.source.name == 'metanetx':
                                
                                ## This is an unequivocal identical reaction
                                identical_rxns.append(rxn)
            
            if len(identical_rxns) > 0:
                print("\nReaction '%s':" % in_reaction.name)
                print("%s" % in_reaction.equation()) 
#                 print(" -> Identical reactions:")
                for rxn in identical_rxns:
                    print(" -> %s" % rxn)
                    print("%s" % (rxn.equation()))
#                     print(" - %s [%d, %s, %s]" % (rxn.equation(), rxn.id, rxn.name, rxn.source))
                    mnx_to_bth_reactions[rxn.name] = in_reaction.name
        
#     print "\n"
#     for mnx_rxn in mnx_to_bth_reactions:
#         print("%10s: %s" % (mnx_rxn, mnx_to_bth_reactions[mnx_rxn]))              
    
    
        
    return mnx_to_bth_reactions
        
        
                          