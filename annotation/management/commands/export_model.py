from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
from libsbml import SBMLDocument, writeSBMLToFile, SBMLReader
import sys, os, re
from myutils.general.utils import loop_counter


class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ Export a model to SBML for a given source ID for exchange.
            
        """ 
        
        
        ## Cycle through command line arguments
        num_args = 0
        for arg in args:
            num_args += 1
        
        model_source_id = args[0]
        try:
            source = Source.objects.get(name=model_source_id)
        except:
            print("There is no such source as '%s', please check ID ..." % model_source_id)
            sys.exit(1) 
        
        
        
        ## Create model container
#         document = SBMLDocument()
#         document.setLevelAndVersion(2,4)
        reader = SBMLReader()
        document = reader.readSBMLFromFile('/Users/wbryant/work/BTH/level2v4_template.xml')
        model = document.getModel()
        model.setName(model_source_id)
        model.setId(model_source_id)
        
        
        ## Get reactions from Metabolic_model
        model_reactions = Metabolic_model.objects.filter()
        
        
        ## Create compartments
        compartments = Compartment.objects.filter(stoichiometry__source=source).distinct()
        
        for compartment in compartments:
            c_model = model.createCompartment()
            c_model.setName(str(compartment.name))
            c_model.setId(str(compartment.id))
            
        
        ## Create Species
        stoichiometries = Stoichiometry.objects.filter(source=source)\
            .values_list(
                "metabolite__id",
                "metabolite__name",
                "compartment__id",
            )\
            .distinct()
        print("There are %d metabolites (with compartments) ..." % len(stoichiometries))
        
        print("Populating model with metabolites ...")
        counter = loop_counter(len(stoichiometries))
        
        
        for met in stoichiometries:
            counter.step()
            species = model.createSpecies()
            species.setName(met[1].encode("utf-8"))
            species.setId(str(met[0] + "__in__" + met[2]))
            species.setCompartment(str(met[2]))
            
        counter.stop()
        
        
        ## Create Reactions (get list according to 'Metabolic_model')
        model_reactions = Metabolic_model.objects.filter(source=source).prefetch_related()
        num_reactions = len(model_reactions)
        
        print("There are %d reactions ..." % num_reactions)
        
        print("Populating model with reactions ...")
        counter = loop_counter(num_reactions)
        
        for mod in model_reactions:
            counter.step()
            reaction = model.createReaction()
            reaction.setName(mod.reaction.name.encode("utf-8"))
            reaction.setId(mod.reaction.name.encode("utf-8"))
            
            if mod.direction.direction == "both":
                reversible = True
            else:
                reversible = False
            reaction.setReversible(reversible)
        
            for sto in mod.reaction.stoichiometry_set.all():
                if sto.stoichiometry > 0:
                    met = reaction.createReactant()
                else:
                    met = reaction.createProduct()
                
                species_id = sto.metabolite.id + "__in__"\
                                + sto.compartment.id
                
                met.setSpecies(str(species_id))
                met.setStoichiometry(abs(sto.stoichiometry))
        
        counter.stop()
            
        ## Set and save the model
        
        print("Writing model to SBML ...")
        document.setModel(model)
#         document.setLevelAndVersion(2,4)
        writeSBMLToFile(document, "/Users/wbryant/work/cogzymes/incognito/test_libsbml.xml")
        
            
        
            
        
        
        
        