'''
Created on 8 Oct 2014

@author: wbryant
'''
from django.db.models import Count, F, Q, Avg, Max

import sys, os
#sys.path.append("/Users/wbryant/git/incognito")
#sys.path.append("/Users/wbryant/git/incognito/annotation_utils")
#sys.path.append("/Users/wbryant/git/incognito/cogzymes")
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

from annotation.models import Source
from cogzymes.models import Reaction_pred, Cogzyme, Gene
from myutils.general.utils import dict_append

def get_gpr_from_reaction(dev_model, reaction, ref_models = None):
    """ Create a GPR string for a particular reaction in a particular dev_model 
        according to the cogzymes in the ref_models predicting that reaction in 
        that dev_model.
    """ 
    
    dev_organism = dev_model.organism
    if not ref_models:
        ref_models = list(Source.objects\
            .filter(reference_model=True)\
            .exclude(organism=dev_organism))
        
    
    ## Get genes for cogzymes catalysing this reaction
    prediction_data = Reaction_pred.objects\
        .filter(
            dev_model=dev_model,
            ref_model__in=ref_models,
            reaction__db_reaction=reaction
        )\
        .values(
            'reaction__mapping__name',
            'reaction__name',
            'ref_model__name',
            'cogzyme__name'
        )
    for pred in prediction_data:
        cogzyme = Cogzyme.objects.get(name=pred['cogzyme__name'])
        locus_cog_data = Gene.objects\
            .filter(
                organism__source=dev_model,
                cogs__cogzyme=cogzyme)\
            .values('locus_tag','cogs__name')
        cog_locus_dict = {}
        for locus_cog in locus_cog_data:
            dict_append(cog_locus_dict,locus_cog['cogs__name'],locus_cog['locus_tag'])

        ## for each cog, create 'or' string
        full_gpr_string = "( "
        cog_gpr_string_list = []
        for cog in cog_locus_dict:
            cog_gpr_string = "( "
            locus_list = sorted(cog_locus_dict[cog])
            locus_string = " or ".join(locus_list)
            cog_gpr_string += locus_string
            cog_gpr_string += " )"
            cog_gpr_string_list.append(cog_gpr_string)
        
        ## Combine all the OR strings into one large AND string
        inner_gpr_string = " and ".join(cog_gpr_string_list)
        full_gpr_string += inner_gpr_string
        full_gpr_string += " )"
        
        return full_gpr_string
        
    
    
    
    
    