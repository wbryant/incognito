from django.core.management.base import BaseCommand, CommandError
from annotation.models import Reaction, Stoichiometry, Reaction_synonym, Metabolite, Metabolite_synonym, Compartment, Source, Metabolic_model, Direction
import sys, os, re
from myutils.general.utils import loop_counter
#from myutils.SBML.import_SBML import import_SBML_to_bipartite as import_SBML
from libsbml import SBMLReader

"""What do I want to achieve with this file?

1.    check for non-MetaNetX reactions and add them to the DB

2.    check that MNX reactions are correct
    -    check stoichiometries
    -    check directionality?
    
"""

def get_note(reaction, name_string):
    
    notes = reaction.getNotesString()
    
    re_string = name_string + ":([^<]+)<"
    
    re_result = re.search(re_string, notes)
    
    if re_result is not None:
        return re_result.group(1).strip()
    else:
        return None
        

class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
            
        
        SBML_filename = '/Users/wbryant/work/BTH/data/Joern/union_model/iAH991__P2M_BT__BioCyc__step_3.xml'
        
        
        ## Clear any previous import from this file and create Source record 
        source_id = SBML_filename.split("/")[-1]
        if Source.objects.filter(name=source_id).count() == 1:
            Source.objects.filter(name=source_id).delete()
        source, _ = Source.objects.get_or_create(name=source_id)
        
        
        """Import Joern's model: assume MetaNetX reactions are the same as in DB.
        
        For each non-MetaNetX reaction, try to find MNX metabolites 
        to do best integration possible, then add reaction and 
        non-MNX metabolites."""
        
        ###! Use SBML to pull out reaction details (met details are implied)
        
        ## Read in SBML file
        reader = SBMLReader()
        document = reader.readSBMLFromFile(SBML_filename)
        model = document.getModel()
        
        ##! For each reaction, find MNX ID and met IDs (with stoichiometry)
        
        idx = 0
        #counter = loop_counter(len(model.getListOfReactions()))
        
        for rxn in model.getListOfReactions():
            
            idx += 1
            #counter.step()
            
            reaction_status = "Complete"
            
            
            ## Get reaction reversibility (and direction)
            model_rxn_id = rxn.getId()
            reversible = rxn.getReversible()
            if reversible == True:
                direction_id = "both"
            else:
                direction_id = "ltr"
            direction = Direction.objects.get(direction=direction_id)
            
            
            ## Get "SOURCE: " and "REACTION: " from notes and find best ID
            note_source_id = get_note(rxn, "SOURCE")
            note_reaction_name = get_note(rxn, "REACTION")
            if note_reaction_name is not None:
                reaction_name = note_reaction_name
            elif note_source_id is not None:
                reaction_name = note_source_id
            else:
                reaction_name = rxn.getId()
            reaction_name = reaction_name.split(";")[0]
            reaction_name = re.sub("^R\_","",reaction_name)
            
            
            ## Is reaction in DB?  If not, create it with ID
            known_reaction = False
            if Reaction.objects.filter(name=reaction_name).count() == 1:
                reaction = Reaction.objects.get(id=reaction_name)
                known_reaction = True
            elif Reaction.objects.filter(reaction_synonym__synonym=reaction_name).distinct().count() > 0:
                reaction = Reaction.objects.filter(reaction_synonym__synonym=reaction_name).distinct()[0]
                known_reaction = True
            
            

            if known_reaction == False:
                continue
                ## Create new reaction and reaction_synonym
                
                reaction = Reaction(
                    id=reaction_name,
                    source=source
                )
                reaction.save()
                reaction_synonym = Reaction_synonym(
                    synonym = reaction_name,
                    reaction = reaction,
                    source=source
                )
                reaction_synonym.save()                
                
                
                ## For each metabolite, try to find in DB and if not present create it, then create stoichiometry entry
                
                metabolites_list = []
                 
                for reactant in rxn.getListOfReactants():
                    metabolites_list.append(("reactant",reactant))
                     
                for product in rxn.getListOfProducts():
                    metabolites_list.append(("product",product))
                     
                
                 
                for metabolite_tuple in metabolites_list:
                     
                    met = metabolite_tuple[1]
                    met_type = metabolite_tuple[0]
                     
                    known_metabolite = False
                    species_id = met.getSpecies()
                     
                    ## Establish species ID and compartment
                    try:
                        u = species_id.split("@")
                        metabolite_id = u[0]
                        compartment_id = u[-1]
                    except:
                        metabolite_id = species_id
                        #print(" - '%s' ID without compartment?" % species_id)
                     
                    ## Get or create metabolite
                    if Metabolite.objects.filter(id=metabolite_id).count() > 0:
                        metabolite = Metabolite.objects.get(id=metabolite_id)
                        known_metabolite = True
                    elif Metabolite.objects.filter(metabolite_synonym__synonym=metabolite_id).count() > 0:
                        try:
                            metabolite = Metabolite.objects.filter(metabolite_synonym__synonym=metabolite_id)[0]
                        except:
                            print(" - %s returns multiple reactions:\n" % metabolite_id)
                            for metabolite in Metabolite.objects.filter(metabolite_synonym__synonym=metabolite_id):
                                print(" - - %s: " % reaction.name)
                            break
                        known_metabolite = True
                    else:
                        metabolite = Metabolite(
                            id=metabolite_id,
                            name=metabolite_id,
                            source=source
                        )
                        metabolite.save()
                        metabolite_synonym = Metabolite_synonym(
                            synonym = metabolite_id,
                            metabolite = metabolite,
                            source=source
                        )
                        metabolite_synonym.save()                    
                    
                    ## Get compartment
                    
                    try:
                        compartment = Compartment.objects.get(id=compartment_id)
                    except:
                        compartment = Compartment(
                            id = compartment_id,
                            name = compartment_id,
                            source = source
                        )
                        compartment.save()
                        
                    ## Get stoichiometric coefficient     
                    coeff = met.getStoichiometry()
                    if met_type == "reactant":
                        coeff = -1*coeff
                    
                    ## Create stoichiometry for unknown reaction
                    
                    stoichiometry = Stoichiometry(
                        reaction=reaction,
                        metabolite=metabolite,
                        source=source,
                        compartment=compartment,
                        stoichiometry=coeff
                    )
                    stoichiometry.save()
               
            else:
                
                ###! Reaction is known - check whether stoichiometries match: if reverse, change direction
                ###! If stoichiometry is wrong, print problem
                
                reaction_stoichiometry = Stoichiometry.objects.filter(reaction=reaction).distinct()
            
                reverse_count = 0
                
                ###! Initially, check for consistency of MNX reactions
                 
                metabolites_list = []
                 
                for reactant in rxn.getListOfReactants():
                    metabolites_list.append(("reactant",reactant))     
                for product in rxn.getListOfProducts():
                    metabolites_list.append(("product",product))
                     
                num_metabolites = len(metabolites_list)
                
                stos_zero_in_DB = []
                 
                for metabolite_tuple in metabolites_list:
                    
                    met = metabolite_tuple[1]
                    met_type = metabolite_tuple[0]
                     
                    known_metabolite = False
                    species_id = met.getSpecies()
                    
                     
                    ## Establish species ID and compartment
                    try:
                        u = species_id.split("@")
                        metabolite_id = u[0]
                        compartment_id = u[-1]
                    except:
                        print("%s (%s): '%s' metabolite ID not formed properly ..." % (reaction.name, model_rxn_id, species_id))
                        continue

                     
                    ## Is metabolite present in DB?
                    if Metabolite.objects.filter(id=metabolite_id).count() > 0:
                        metabolite = Metabolite.objects.get(id=metabolite_id)
                    elif Metabolite.objects.filter(metabolite_synonym__synonym=metabolite_id).count() > 0:
                        metabolite = Metabolite.objects.get(metabolite_synonym__synonym=metabolite_id)
                    else:
                        print("%s (%s): %s '%s' metabolite ID not found in DB ..." % (reaction.name, model_rxn_id, met_type, metabolite_id))
                        continue
#                         metabolite = Metabolite(id=metabolite_id, source=source)
#                         metabolite.save()
#                         metabolite_synonym = Metabolite_synonym(
#                             synonym = metabolite_id,
#                             metabolite = metabolite,
#                             source = source
#                         )
#                         metabolite_synonym.save()                    
                    
                    
                    ## Get stoichiometric coefficient     
                    coeff = met.getStoichiometry()
                    if met_type == "reactant":
                        coeff = -1*coeff
                    
                    ## Check metabolite presence and stoichiometry
                    num_stos = reaction_stoichiometry.filter(metabolite=metabolite).count() 
                    if num_stos > 0:
                        
                        if num_stos == 1:
                            sto_record = reaction_stoichiometry \
                                .get(metabolite=metabolite) 
                        else:
                            if met_type == "reactant":
                                if reaction_stoichiometry.filter(metabolite=metabolite, stoichiometry__lt=0).count() == 1:
                                    sto_record = reaction_stoichiometry \
                                        .filter(metabolite=metabolite, stoichiometry__lt=0)[0]
                                else:
                                    print("%s (%s): %s '%s' found multiple times, cannot distinguish ..." % (reaction.name, model_rxn_id, met_type, metabolite_id))
                                    continue
                            else:
                                if reaction_stoichiometry.filter(metabolite=metabolite, stoichiometry__gt=0).count() == 1:
                                    sto_record = reaction_stoichiometry \
                                        .filter(metabolite=metabolite, stoichiometry__gt=0)[0] 
                                else:
                                    print("%s (%s): %s '%s' found multiple times, cannot distinguish ..." % (reaction.name, model_rxn_id, met_type, metabolite_id))
                                    continue
                        
                        sto = sto_record.stoichiometry
                        
                        if sto == -1*coeff:
                            reverse_count += 1
                        elif sto != coeff:
                            if sto == 0:
                                ## Correct now!
                                stos_zero_in_DB.append((sto_record, coeff))
                                print stos_zero_in_DB[-1]
                                
                            print("%s (%s): %s '%s' - model coeff = %d, DB coeff = %d ..." % (reaction.name, model_rxn_id, met_type, metabolite_id, coeff, sto))
                            continue
                        
                            
                    else:
                        print("%s (%s): %s '%s' not found in this reaction ..." % (reaction.name, model_rxn_id, met_type, metabolite_id))
                        continue
                
                if reverse_count > 0:
                    if reverse_count != num_metabolites:
                        print("%s (%s): metabolites mixed up, forward and reverse (%d/%d reverse count)!" % (reaction.name, model_rxn_id, reverse_count, num_metabolites))
                    else:
                        ## Add zeroed metabolites with reverse coeff
                        
                        for sto_tuple in stos_zero_in_DB:
                            print sto_tuple
                            sto_record = sto_tuple[0]
                            sto_record.stoichiometry = -1*sto_tuple[1]
                            sto_record.source = source 
                            sto_record.save()
                            
                        #print("%s (%s): reaction is reversed ..." % (reaction.name, model_rxn_id))
                else:
                    ## Add zeroed metabolites with reverse coeff
                        
                        for sto_tuple in stos_zero_in_DB:
                            print sto_tuple
                            sto_record = sto_tuple[0]
                            sto_record.stoichiometry = sto_tuple[1]
                            sto_record.source = source 
                            sto_record.save()
                    
                    #print("%s (%s): reaction is correct ..." % (reaction.name, model_rxn_id))    


#             ## Add metabolic model reference to Metabolic_model
#             
#             model_reaction = Metabolic_model(
#                 source=source,
#                 reaction=reaction,
#                 direction=direction
#             )
#             model_reaction.save()
            
            
               
        #counter.stop()       
                
            
#             if known_reaction == True:
#                 
#                 #print(" - found with ID '%s', DB Reaction '%s'" % (reaction_name, reaction.name))
#                 
#                 reaction_stoichiometry = Stoichiometry.objects.filter(reaction=reaction)
#                 
# #                 ## Create tuples for each metabolite for comparison of stoichiometries
# #                 sto_tuples_model = []
# #                 sto_tuples_reverse = []
# #                 sto_tuple_comp_dict = {}
#                 
#                
#                 ###! Initially, check for consistency of MNX reactions
#                 
#                 metabolites_list = []
#                 
#                 for reactant in rxn.getListOfReactants():
#                     metabolites_list.append(("reactant",reactant))
#                     
#                 for product in rxn.getListOfProducts():
#                     metabolites_list.append(("product",product))
#                     
#                 
#                 for metabolite_tuple in metabolites_list:
#                     
#                     met = metabolite_tuple[1]
#                     met_type = metabolite_tuple[0]
#                     
#                     known_metabolite = False
#                     species_id = met.getSpecies()
#                     
#                     ## Establish species ID and compartment
#                     try:
#                         u = species_id.split("@")
#                         metabolite_id = u[0]
#                         compartment_id = u[-1]
#                     except:
#                         metabolite_id = species_id
#                         #print(" - '%s' ID without compartment?" % species_id)
#                     
#                     ## Is metabolite present in DB?
#                     if Metabolite.objects.filter(id=metabolite_id).count() > 0:
#                         metabolite = Metabolite.objects.get(id=metabolite_id)
#                         known_metabolite = True
#                     elif Metabolite.objects.filter(metabolite_synonym__synonym=metabolite_id).count() > 0:
#                         metabolite = Metabolite.objects.get(metabolite_synonym__synonym=metabolite_id)
#                         known_metabolite = True
#                     else:
#                         reaction_status = "Metabolite Not Found"
#                         #print(" - %s '%s' not found in DB ..." % (met_type, metabolite_id))
# #                         metabolite = Metabolite(id=metabolite_id)
# #                         metabolite.save()
# #                         metabolite_synonym = Metabolite_synonym(
# #                             synonym = metabolite_id,
# #                             metabolite = metabolite
# #                         )
# #                         metabolite_synonym.save()                    
#                     
#                     ## If present, check stoichiometry
#                     if known_metabolite == True:
#                         
#                         coeff = met.getStoichiometry()
#                         if met_type == "reactant":
#                             coeff = -1*coeff
#                         
#                         if reaction_stoichiometry.filter(metabolite=metabolite).count() == 1:
#                             sto = reaction_stoichiometry \
#                                     .get(metabolite=metabolite) \
#                                     .stoichiometry
#                             
#                             if sto != coeff:
#                                 #print(" - %s '%s' - model coeff = %d, DB coeff = %d ..." % (met_type, metabolite_id, coeff, sto))
#                                 reaction_status = "Stoichiometry Incorrect"
# #                             else:
# #                                 print(" - Substrate '%s' is correct ..." % (reaction_name, metabolite_id))
#                         else:
#                             #print(" - %s '%s' not found in DB reaction ..." % (met_type, metabolite_id))
#                             reaction_status = "Metabolite Not Found"
                
#             print reaction_status
            
            
###! Add iAH991 reaction stoichiometries

###! Should I be swapping the model reactions?  Only for checking forward/backward.  
###! All of this is validation, if reactions are correct / inputed extraneous ones
###! then the only required information is directionality for creating my own model

###! Where and how should this model be kept?  Probably a new table with sto, reversibility.

                
            
        
        
        
        
        
        
        
        
        