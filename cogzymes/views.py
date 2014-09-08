# Create your views here.

from django.shortcuts import render_to_response
from annotation.models import Model_reaction, Source, Model_metabolite, Reaction_group, Reaction
from cogzymes.models import Reaction_pred, Cogzyme, Gene
from django.db.models import Count
from myutils.general.utils import dict_append, preview_dict

def home(request):
    
    model_specified = request.session.get('model_specified') 
 
    model_data = []
    for model in Source.objects.filter(organism__isnull = False):
        model_dict = {}
        model_dict['model_id'] = model.name
        model_dict['tax_id'] = model.organism.taxonomy_id
        model_dict['Number_of_Reactions'] = Model_reaction.objects.filter(source=model).count()
        model_dict['Number_of_Metabolites'] = Model_metabolite.objects.filter(source=model).count()
        model_dict['Number_of_Predictions'] = Reaction_pred.objects.filter(dev_model=model).count()
        model_data.append(model_dict)
#         print("{}, {}, {}".format(
#             model_data[-1]['model_id'],
#             model_data[-1]['tax_id'],
#             model_data[-1]['Number_of_Predictions']
#         ))
        
    if len(model_data) == 0:
        model_data = None
    
    return render_to_response('home.html', {
        'model_data': model_data,
        'model_specified': model_specified
    })
    

def model(request, model_specified = None):
    
    #model_specified = request.session.get('model_specified')
    
    if not model_specified:
        ## Is model already specified?
        model_specified = request.session.get('model_specified')
        if not model_specified:
            model_unselected(request)
    
    try:
        source = Source.objects.get(name=model_specified)
        request.session['model_specified'] = model_specified
    except:
        return render_to_response('model_not_found.html', {'model_specified': model_specified})
        
    
#     model_reactions = Model_reaction.objects.filter(source=source)
#     reaction_preds = Reaction_pred.objects.filter(dev_model=source)
#     rxn_equivalents = {}
#     for rxn in model_reactions:
#         rxn_equivalents[rxn.model_id] = Model_reaction.objects.filter(mapping__model_reaction=rxn).distinct().count()
 
    ## Get data for Model Reactions Tab
    model_rxns_data = Model_reaction.objects\
        .filter(source=source)\
        .annotate(equiv_count=Count('mapping__model_reaction'))\
        .values('model_id','name','gpr','db_reaction__name','equiv_count')
    for rxn_data in model_rxns_data:
        rxn_data['equiv_count'] -= 1
        if rxn_data['equiv_count'] < 0:
            rxn_data['equiv_count'] = 0
    
    ## Get data for Reaction Prediction tab
    prediction_data = Reaction_pred.objects\
        .filter(dev_model=source)\
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
                organism__source=source,
                cogs__cogzyme=cogzyme)\
            .values('locus_tag','cogs__name')
        cog_locus_dict = {}
        for locus_cog in locus_cog_data:
            dict_append(cog_locus_dict,locus_cog['cogs__name'],locus_cog['locus_tag'])
         
        cog_locus_list = []
        for cog in cog_locus_dict:
            locus_list = sorted(cog_locus_dict[cog])
            locus_string = ", ".join(locus_list)
            cog_locus_list.append([cog, locus_string])
         
        cog_locus_list.sort(key=lambda x: x[0])
        pred['cog_locus_list'] = cog_locus_list       
    
    summary = {}
    
    num_preds = Source.objects\
        .filter(ref_model_preds__dev_model=source)\
        .count()
    summary['num_preds'] = num_preds
    
    num_adds = Reaction.objects\
        .filter(
            model_reaction__reaction_pred__dev_model=source,
            model_reaction__reaction_pred__status='add')\
        .distinct().count()
    summary['num_adds'] = num_adds
    
    num_rems = Reaction.objects\
        .filter(
            model_reaction__reaction_pred__dev_model=source,
            model_reaction__reaction_pred__status='rem')\
        .distinct().count()
    summary['num_rems'] = num_rems
    
    
    adds_list = Source.objects\
        .filter(
            ref_model_preds__dev_model=source,
            ref_model_preds__status='add')\
        .annotate(Count('ref_model_preds'))\
        .values_list('name','ref_model_preds__count')
    rems_list = Source.objects\
        .filter(
            ref_model_preds__dev_model=source,
            ref_model_preds__status='rem')\
        .annotate(Count('ref_model_preds'))\
        .values_list('name','ref_model_preds__count')
    ref_models = {}
    for adds in adds_list:
        if adds[0] not in ref_models:
            ref_models[adds[0]] = {}
        ref_models[adds[0]]['adds'] = adds[1]
    for rems in rems_list:
        if rems[0] not in ref_models:
            ref_models[rems[0]] = {}
        ref_models[rems[0]]['rems'] = rems[1]
    ref_model_list = []
    for model in ref_models:
        if 'rems' not in ref_models[model]:
            ref_models[model]['rems'] = 0
        if 'adds' not in ref_models[model]:
            ref_models[model]['adds'] = 0
        ref_model_list.append([model, ref_models[model]['adds'], ref_models[model]['rems']])
    summary['ref_model_list'] = ref_model_list
       
    return render_to_response('model.html', {                                  
        'model_rxns_data': model_rxns_data,
        'model_specified': model_specified,
        'prediction_data': prediction_data,
        'summary':  summary
    })

    
#     return render_to_response('model.html', {
#         'source': source, 
#         'model_rxns': model_reactions, 
#         'pred_rxns': reaction_preds,
#         'rxn_equivalents': rxn_equivalents
#     })

def model_unselected(request):
    return render_to_response('model_unselected.html')