from django.core.management.base import BaseCommand, CommandError
from cogzymes.models import Cog, Cogzyme, Gene, Enzyme, Cogzyme, Enzyme_type, Reaction_pred
from annotation.models import Source, Model_reaction
import sys, os, re


def create_cog_type_dict(source):
    """Create dict of cogs saying whether they are in model or just in genome."""
    
    cog_type_dict = {}
    
    organism_cogs = []
    model_cogs = []
    
    for cog in Cog.objects.filter(gene__organism=source.organism).distinct():
        organism_cogs.append(cog)
        
    for cog in Cog.objects.filter(cogzyme__enzymes__source=source).distinct():
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
    
    cogs = [cog for cog in cogzyme.cogs.all()]
    
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

def create_reaction_prediction(reaction, addrem, dev_source, ref_source, cogzyme, type):
    """
    Create Reaction_pred from details
    """
    
    reaction_pred = Reaction_pred(
        dev_model = dev_source,
        ref_model = ref_source,
        reaction = reaction,
        status = addrem,
        num_enzymes = 0,
        cogzyme = cogzyme,
        type = type
    )
    try:
        reaction_pred.save()
    except:
        print("Reaction prediction '{}' for '{}' failed to save ..."
              .format(reaction.name, cogzyme.name))
    

class Command(BaseCommand):
    
    help = 'Find all reactions inferred by InCOGnito between a reference and a development model.'
        
    def handle(self, *args, **options):
        
        """ Find all reactions inferred by InCOGnito between a reference and a development model.
            
            N.B. Reactions are currently limited by:
            1)    Lack of manual mappings (all done via MNX),
            2)    Reactions will only be exported if MNX reaction found
            
            
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
            dev_organism = dev_source.organism
            print("Development model, ID {}, found, containing {} reactions ...".format(dev_id, num_reactions))
        except:
            print("Development Source could not be found, exiting ...")
            
        try:
            ref_source = Source.objects.get(name=ref_id)
            num_reactions = Model_reaction.objects.filter(source=ref_source).count()
            ref_organism = ref_source.organism
            print("Reference model, ID {}, found, containing {} reactions ...".format(ref_id, num_reactions))
        except:
            print("Reference Source could not be found, exiting ...")
        
        
        ## Delete any previous inferences from these dev and ref models
        
        Reaction_pred.objects.filter(dev_model=dev_source,ref_model=ref_source).delete()
        
        ## Create dict of cogs saying whether they are in dev_model or just in dev_genome
        
        dev_cog_types = create_cog_type_dict(dev_source)
        
#         dev_rxns_full = [rxn for rxn in Model_reaction.objects.filter(source = dev_source).distinct()]
        
        ## For each cogzyme in the ref_model, can the dev_genome make it?
        
        for ref_cogzyme in Cogzyme.objects.filter(enzymes__source=ref_source).distinct():
            
            ref_cogzyme_type = cogzyme_in_model(ref_cogzyme, dev_cog_types)
            
            #print ref_cogzyme.name, ref_cogzyme_type
            
            if ref_cogzyme_type == 'model':
                ## cogzyme possible with genes already in the model
                
                if ref_cogzyme.enzymes.filter(source=dev_source):
                    ## Already in model - KNOWN
        
                    
                    ## Find rxns missing in dev_model
                    ref_rxns_missing_in_dev = [(rxn, 'add') for rxn in Model_reaction.objects
                                               .filter(cog_enzymes__cogzyme=ref_cogzyme, source=ref_source, db_reaction__isnull=False)
                                               .exclude(db_reaction__model_reaction__source=dev_source)
                                               .distinct()]
                    
        
                    ## Those only in dev
                    dev_rxns_extra = [(rxn, 'rem') for rxn in Model_reaction.objects
                                               .filter(cog_enzymes__cogzyme=ref_cogzyme, source=dev_source, db_reaction__isnull=False)
                                               .exclude(db_reaction__model_reaction__source=ref_source)
                                               .distinct()]
                
                    
                    ## Add predictions
                    
                    all_preds = ref_rxns_missing_in_dev + dev_rxns_extra
                    for pred in all_preds:
                        create_reaction_prediction(pred[0], pred[1], dev_source, ref_source, ref_cogzyme, 'mod')
                    
                    pass
                
                else:
                    ## Can be created from model genes - SUSPECT
                    
                    ## Look at ref_reactions and if they are not present in dev_model add them to reaction_preds
                    
                    ## Find rxns missing in dev_model
                    suspect_preds = [(rxn, 'add') for rxn in Model_reaction.objects
                                               .filter(cog_enzymes__cogzyme=ref_cogzyme, source=ref_source, db_reaction__isnull=False)
                                               .exclude(db_reaction__model_reaction__source=dev_source)
                                               .distinct()]
                    
                    for pred in suspect_preds:
                        create_reaction_prediction(pred[0], pred[1], dev_source, ref_source, ref_cogzyme, 'sus')
                    
                    pass
            
            elif ref_cogzyme_type == 'genome':
                ## Can be created from genome genes
                
                ## Look at ref_reactions and if they are not present in dev_model add them to reaction_preds 
                
                hidden_preds = [(rxn, 'add') for rxn in Model_reaction.objects
                                           .filter(cog_enzymes__cogzyme=ref_cogzyme, source=ref_source, db_reaction__isnull=False)
                                           .exclude(db_reaction__model_reaction__source=dev_source)
                                           .distinct()]
                
                for pred in hidden_preds:
                    create_reaction_prediction(pred[0], pred[1], dev_source, ref_source, ref_cogzyme, 'hid')
                
                
                pass
            