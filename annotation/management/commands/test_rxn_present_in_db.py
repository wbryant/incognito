from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter
from collections import OrderedDict

class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        file_in = '/Users/wbryant/work/BTH/analysis/cogzymes/theo/candidates_filter3.csv'
        file_row_list = []
        f_in = open(file_in, 'r')
        for line in f_in:
            file_row_list.append(line.split("\t"))
        
#         reaction_id_list = ['3NTD2pp', '3NTD4pp']
        
#         reaction_id_list = map(list, zip(*file_row_list))[0]
        
        Cogzyme_prediction.objects.all().delete()
        
        reactions_not_found = []
        
        for row in file_row_list: 
        
            reaction_id = row[0]
            
#             if reaction_id[-2:] != "pp":
            
            ## Try to find reaction
            
#             print("{}:".format(reaction_id))
            
            try:
                reaction_syn = Reaction_synonym.objects.get(synonym=reaction_id)
                reaction = reaction_syn.reaction
            except:
                ## Maybe non-periplasmic
                if reaction_id[-2:] == "pp":
                    reaction_id = reaction_id[:-2]
                    try:
                        reaction_syn = Reaction_synonym.objects.get(synonym=reaction_id)
                        reaction = reaction_syn.reaction
                    except:
#                         print(" - No unique reaction found ...")
                        reactions_not_found.append(reaction_id)
                        continue
        
#             print(" - Reaction ID '{}' corresponds to reaction {}".format(reaction_id, reaction.name))
            
            ## Look at stoichiometry and determine whether the reaction is complete in the DB.
            
            stoichiometries = Stoichiometry.objects.filter(reaction=reaction)
            
            complete = True
            
            for sto in stoichiometries:
                if sto.compartment is None:
                    complete = False
                    
            if complete == True:
                ### Add reaction to Cogzyme results
                
                cog_field_in = row[1]
                cog_field_in = cog_field_in.replace("*","")
                cog_field_in = cog_field_in.replace("!","")                    
                
                gpr_in = row[2].strip()

                 
                ## Format the GPR
                
                gpr = re.sub("\'","",gpr_in)
                gpr = re.sub("\]\], \[\[",") or (",gpr)
                gpr = re.sub("\], \[",") and (",gpr)
                gpr = re.sub(", "," or ",gpr)
                gpr = re.sub("^\[{3}","(",gpr)
                gpr = re.sub("\]{3}$",")",gpr)
                
                ## Remove duplicates (from, say, multiple COG membership of genes)
                
                gpr_subunits = gpr.split(" and ")
                gpr_subunits = list(OrderedDict.fromkeys(gpr_subunits))
                gpr = " and ".join(gpr_subunits)
                
                ## Remove unnecessary brackets
                
                gpr_parts = gpr.split(" or ")
                gpr_parts_new = []
                
                for entry in gpr_parts:
                    if "and" not in entry:
                        entry = re.sub("^\((.+)\)$","\g<1>",entry)
                    gpr_parts_new.append(entry)
                    
                gpr = " or ".join(gpr_parts_new)
                gpr = re.sub("^\(([^\(\)]+)\)$","\g<1>",gpr)
                
                if ("and" not in gpr) or ("or" not in gpr):
                    ## All 'or's or 'and's, so remove all brackets
                    gpr = re.sub("[\(\)]","",gpr)
                    
                
#                 print(" - {}".format(gpr))
                
                
                ## Format the Cogzyme
                
                cog_field = re.sub("', '",") or (",cog_field_in)
                cog_field = re.sub(","," and ",cog_field)
                cog_field = re.sub("\['","(",cog_field)
                cog_field = re.sub("'\]",")",cog_field)
                
#                 print(" - {}".format(cog_field))
                
                
                ## Import prediction into database
                
                pred = Cogzyme_prediction(
                            gpr = gpr,
                            cog_field = cog_field,
                            reaction = reaction)
                pred.save()
#                 print(" - Prediction saved ...\n")
                
            else:
                ## Stoichiometry not complete    
                
                reactions_not_found.append(reaction_id)
#                 print(" - Stoichiometry incomplete, so cannot be used ...\n")
                
        print("Reactions not found ({}):".format(file_in))
        for rxn in reactions_not_found:
            print("{}".format(rxn))
        
        
        ## Cycle through command line arguments
        num_args = 0
        for arg in args:
            num_args += 1
        
                    