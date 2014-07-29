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
    """Retrieve a named note in a libSBML reaction."""
    
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
            
        
        SBML_filename = '/Users/wbryant/work/BTH/data/iAH991/BTH_with_gprs.xml'
        
        
        ## Clear any previous import from this file and create Source record 
        source_name = SBML_filename.split("/")[-1]
        if Source.objects.filter(name=source_name).count() > 0:
            Source.objects.filter(name=source_name).delete()
            
        source = Source(name=source_name)
        source.save()
        
        """Import Joern's model: assume model has correct stoichiometry, so override DB.
        
        For each non-MetaNetX reaction, try to find MNX metabolites 
        to do best integration possible, then add reaction and 
        non-MNX metabolites."""
        
        ### Use SBML to pull out reaction details (met details are implied)
        
        ## Read in SBML file
        reader = SBMLReader()
        document = reader.readSBMLFromFile(SBML_filename)
        model = document.getModel()
        
        idx = 0
        counter = loop_counter(len(model.getListOfReactions()))
        
        for rxn in model.getListOfReactions():
            
            idx += 1
            counter.step()
            
            
            ## Get reaction reversibility (and direction)
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
                ## Has MNX ID
                reaction_name = note_reaction_name
            elif note_source_id is not None:
                ## Has alternative ID
                reaction_name = note_source_id
            else:
                reaction_name = rxn.getId()
            reaction_name = reaction_name.split(";")[0]
            reaction_name = re.sub("^R\_","",reaction_name)
            
            
            ## Create new reaction
            new_reaction = Reaction(
                name=reaction_name,
                source=source,
            )
            new_reaction.save()
            
            ## Get all old synonyms for this reaction ID and point them towards the model reactions
            for synonym in Reaction_synonym.objects.filter(reaction__name=reaction_name):
                synonym.reaction = new_reaction
                synonym.save()
            
            try:
                synonym = Reaction_synonym.objects.get(synonym=reaction_name)
                synonym.reaction = new_reaction
                synonym.save()
            except:    
                new_reaction_synonym = Reaction_synonym(
                    synonym = reaction_name,
                    reaction = new_reaction,
                    source = source
                )
                new_reaction_synonym.save()
                
            
            ## Create list of all participants in reaction
            metabolites_list = []
            for reactant in rxn.getListOfReactants():
                metabolites_list.append(("reactant",reactant))                     
            for product in rxn.getListOfProducts():
                metabolites_list.append(("product",product))
                  
             
            ### For each reactant and product, create stoichiometry
            for metabolite_tuple in metabolites_list:
                  
                met = metabolite_tuple[1]
                met_type = metabolite_tuple[0] 
                species_id = met.getSpecies()
                  
                ## Establish species ID and compartment
                try:
                    u = species_id.split("__64__")
                    metabolite_id = u[0]
                    compartment_id = u[1]
                except:
                    metabolite_id = species_id
                    print(" - '%s' ID without compartment?" % species_id)
                  
                ## Get or create metabolite
                if Metabolite.objects.filter(id=metabolite_id).count() == 1:
                    metabolite = Metabolite.objects.get(id=metabolite_id)
                elif Metabolite.objects.filter(metabolite_synonym__synonym=metabolite_id).distinct().count() == 1:
                    metabolite = Metabolite.objects.filter(metabolite_synonym__synonym=metabolite_id).distinct()[0]
                else:
                    ## There may be multiple entries with the same synonym, so eliminate the synonyms
                    Metabolite_synonym.objects.filter(synonym=metabolite_id).delete()
                    
                    ## Create new metabolite with ID metabolite_id
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
                    try:
                        compartment.save()
                    except:
                        print compartment.id
                        print compartment.name
                        print compartment.source
                        sys.exit(1)
                     
                     
                ## Get stoichiometric coefficient     
                coeff = met.getStoichiometry()
                if met_type == "reactant":
                    coeff = -1*coeff
                 
                ## Create stoichiometry for reaction
                stoichiometry = Stoichiometry(
                    reaction = new_reaction,
                    metabolite = metabolite,
                    source = source,
                    compartment = compartment,
                    stoichiometry = coeff
                )
                stoichiometry.save()
            
            ## Now that reaction is imported, add to Metabolic_model with directionality
            model_reaction = Metabolic_model(
                source = source,
                reaction = new_reaction,
                direction = direction
            )
            model_reaction.save()
        
        counter.stop()    
        
        
        
        
        
        
        
        
        