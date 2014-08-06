from django.core.management.base import BaseCommand, CommandError
from cogzymes.models import Cog, Cogzyme, Gene, Enzyme, Cogzyme, Enzyme_type, Reaction_preds
from annotation.models import Source, Model_reaction
import sys, os, re


def create_cog_type_dict(source):
    """Create dict of cogs saying whether they are in model or just in genome."""
    
    cog_type_dict = {}
    
    organism_cogs = []
    model_cogs = []
    
    for cog in Cog.objects.filter(gene_set__organism=source.organism).distinct():
        organism_cogs.append(cog)
        
    for cog in Cog.objects.filter(cogzyme_set__enzymes__source=source).distinct():
        model_cogs.append(cog)
        
    for cog in organism_cogs:
        if cog in model_cogs:
            cog_type_dict[cog] = 'model'
        else:
            cog_type_dict[cog] = 'genome'
    
    return cog_type_dict


def cogzyme_in_model(cogzyme, cog_type_dict):
    """Determine cogzyme presence in a metabolic model.
    Can cogzyme be made up by genes in the modelled organism, 
    done using cogTypeDict for specific model?
    """
    
    cogs = [cog for cog in cogzyme.cogs]
    
    cogzyme_model = True
    
    for cog in cogs:
        if cog in cog_type_dict:
            if cog_type_dict[cog] == 'genome':
                cogzyme_model = False
        else:
            return None
    
    if cogzyme_model == True:
        return 'model'
    else:
        return 'genome'
    
class Command(BaseCommand):
    
    help = 'Find all reactions inferred by InCOGnito between a reference and a development model.'
        
    def handle(self, *args, **options):
        
        """ Find all reactions inferred by InCOGnito between a reference and a development model.
            
        """ 
        
        ## Get model IDs from command line.
        
        if len(args) <> 2:
            print("Two model IDs must be supplied with the command.")
            sys.exit(1)
        else:
            dev_id = args[0]
            ref_id = args[1]
        
        
        ## Check sources
    
        try:
            dev_source = Source.objects.get(name=dev_id)
            num_reactions = Model_reaction.objects.filter(source=dev_source).count()
            print("Development model, ID {}, found, containing {} reactions ...".format(dev_id, num_reactions))
        except:
            print("Development Source could not be found, exiting ...")
            
        try:
            ref_source = Source.objects.get(name=ref_id)
            num_reactions = Model_reaction.objects.filter(source=ref_source).count()
            print("Reference model, ID {}, found, containing {} reactions ...".format(dev_id, num_reactions))
        except:
            print("Reference Source could not be found, exiting ...")

        
        ## Create dict of cogs saying whether they are in dev_model or just in dev_genome
        
        dev_cog_types = create_cog_type_dict(dev_source)
        
        
        ## For each cogzyme in the ref_model, can the dev_genome make it?
        
        for ref_cogzyme in Cogzyme.objects.filter(enzymes__source=ref_source).distinct():
            ref_cogzyme_type = cogzyme_in_model(ref_cogzyme, dev_cog_types)
            
            if ref_cogzyme_type == 'model':
                ## cogzyme possible with genes already in the model
                
                if dev_source in ref_cogzyme.enzymes.source
            
        
        ## if it can:
        
        ## - if it is already a cogzyme in dev_model:
        
        ## - - find rxns missing in dev_model and add to reaction_preds
        
        ## - - find rxns only in dev_model and add to reaction_preds
        
        ## - elif all cogs in dev_model (suspect):
        
        ## - - look at ref_reactions and if they are not present in dev_model add them to reaction_preds 
        
        ## - elif all cogs in dev_genome (hidden):

        ## - - look at ref_reactions and if they are not present in dev_model add them to reaction_preds 
                
                
                