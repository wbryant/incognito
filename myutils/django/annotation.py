'''
Created on 11 Mar 2014

@author: wbryant
'''

from django.db.models import Count, F, Q, Avg, Max

import sys, os
sys.path.append("/Users/wbryant/work/BTH/incognito")
sys.path.append("/Users/wbryant/work/BTH/incognito/annotation")
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
#from annotation.models import Reaction, Metabolite, Stoichiometry
# from annotation.models import Reaction, Metabolite, Stoichiometry, Model_reaction

# def find_reaction_overlaps(in_reaction, source = None):
#     """
#     For a reaction, find and print out all reactions overlapping by more than one metabolite, starting with highest overlap.
#     """
#     
#     if source is not None:
#         try:
#             in_reaction = Reaction.objects.get(name=in_reaction, source=source)
#         except:
#             print("Reaction not found ...")
#             sys.exit(1)
#     
#     ### Get list of stoichiometries for reactions sharing two or more metabolites with the reaction
#     
#     print("Reaction '%s':\n" % in_reaction.name)
#     print(" - %s\n" % in_reaction.equation())
#     
#     num_mets = Stoichiometry.objects.filter(reaction=in_reaction).count()
#     
#     overlaps_found = False
#     equivalent_rxns = True
#     
#     while not overlaps_found:
#         overlap_rxns = Reaction.objects\
#             .filter(stoichiometry__metabolite__in 
#                     = Metabolite.objects
#                         .filter(stoichiometry__reaction=in_reaction)
#                         .distinct())\
#             .annotate(num_mets_overlap=Count('id'))\
#             .distinct()\
#             .filter(num_mets_overlap=num_mets)\
#             .exclude(name=in_reaction.name)
#         
#         num_mets -= 1
#         
#         
#         if equivalent_rxns:
#             equivalent_rxns = False
#         else:
#             if (overlap_rxns.count() > 0):
#                 overlaps_found = True
#                 
#         for rxn in overlap_rxns:
#                 ## Get stoichiometry, and print out in the form of a reaction equation
#                 
#                 print("'%s': %s" % (rxn.name, rxn.equation()))
#                 

def find_model_crossover_reactions(model1_source_name, model2_source_name, Model_reaction):
    """
    Find all reactions (and metabolites LATER!!!) that can be mapped between two models.
    """
    
    model1_mapped = Model_reaction.objects.filter(source__name=model1_source_name, db_reaction__isnull=False).values_list("model_id","db_reaction__name").distinct()
    model2_mapped = Model_reaction.objects.filter(source__name=model2_source_name, db_reaction__isnull=False).values_list("model_id","db_reaction__name").distinct()
    
    ## Create dictionary from model1 ID to MNX ID
    model1_mnx_dict = {}
    for entry in model1_mapped:
        model1_mnx_dict[entry[0]] = entry[1]
    
    
    ## Create dictionary from MNX ID to model2 ID
    mnx_model2_dict = {}
    for entry in model2_mapped:
        mnx_model2_dict[entry[1]] = entry[0]
        
    
    ## Print the crossover
    for entry in model1_mnx_dict:
        mnx1 = model1_mnx_dict[entry]
        
        if mnx1 in mnx_model2_dict:
            m1_name = entry
            m2_name = mnx_model2_dict[mnx1]
            print("{}\t{}".format(m1_name,m2_name))
    


          
             
if __name__ == '__main__':
    pass