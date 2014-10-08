# Create your views here.

from django.shortcuts import render_to_response
from annotation.models import Model_reaction, Source, Model_metabolite, Reaction_group, Reaction
from cogzymes.models import Reaction_pred, Cogzyme, Gene, Enzyme, Cog
from django.db.models import Count
from myutils.general.utils import dict_append, preview_dict

def home(request):
    
    model_specified = request.session.get('model_specified')
    cogzyme_specified = request.session.get('cogzyme_specified')
    cog_specified = request.session.get('cog_specified')
    cogzyme_short_name = request.session.get('cogzyme_short_name')
 
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
        'model_specified': model_specified,
        'cog_specified': cog_specified,
        'cogzyme_specified': cogzyme_specified,
        'cogzyme_short_name': cogzyme_short_name
    })


   

def model(request, model_specified = None):

    cogzyme_specified = request.session.get('cogzyme_specified')
    cog_specified = request.session.get('cog_specified')
    cogzyme_short_name = request.session.get('cogzyme_short_name')
    
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
        'cog_specified': cog_specified,
        'cogzyme_specified': cogzyme_specified,
        'prediction_data': prediction_data,
        'summary':  summary,
        'cogzyme_short_name': cogzyme_short_name
    })
#     return render_to_response('model.html', {
#         'source': source, 
#         'model_rxns': model_reactions, 
#         'pred_rxns': reaction_preds,
#         'rxn_equivalents': rxn_equivalents
#     })


def model_unselected(request):
    return render_to_response('model_unselected.html')

def cogzyme(request, cogzyme_specified = None):

    ## Keep track of current selections
    model_specified = request.session.get('model_specified')
    cog_specified = request.session.get('cog_specified')
    
    ## Determine whether COGzyme is already specified
    if not cogzyme_specified:
        ## Is cogzyme already specified?
        cogzyme_specified = request.session.get('cogzyme_specified')
        if not cogzyme_specified:
            render_to_response('cogzyme_unselected.html')
    
    ## Is specified value valid?
    try:
        cogzyme = Cogzyme.objects.get(name=cogzyme_specified)
        request.session['cogzyme_specified'] = cogzyme_specified
    except:
        return render_to_response('cogzyme_not_found.html', {'cogzyme_specified': cogzyme_specified})
    
    ## Get COGzyme data
    cogzyme_data = {}
    cogzyme_data['name'] = cogzyme.name
    cogzyme_short_name = cogzyme.name
    if len(cogzyme.name) > 22:
        cogzyme_short_name = cogzyme.name[:18] + " ..."
    
    request.session['cogzyme_short_name'] = cogzyme_short_name
    
    enzyme_list_for_cogzyme = Enzyme.objects.filter(cogzyme=cogzyme)\
        .values('name', 'source__name')
    cogzyme_data['enzymes'] = enzyme_list_for_cogzyme
    
    cog_list_for_cogzyme = Cog.objects.filter(cogzyme=cogzyme)\
        .values_list('name', flat=True)
    cogzyme_data['cogs'] = cog_list_for_cogzyme
    
    model_rxns_data = Model_reaction.objects\
        .filter(cog_enzymes__cogzyme=cogzyme)\
        .annotate(equiv_count=Count('mapping__model_reaction'))\
        .values('model_id','name','gpr','db_reaction__name','equiv_count')
    
    
    return render_to_response('cogzyme.html', {
        'model_rxns_data': model_rxns_data,
        'cogzyme_data': cogzyme_data,
        'model_specified': model_specified,
        'cog_specified': cog_specified,
        'cogzyme_specified': cogzyme_specified,
        'cogzyme_short_name': cogzyme_short_name
    })





def cog(request, cog_specified = None):
    
    model_specified = request.session.get('model_specified')
    cogzyme_specified = request.session.get('cogzyme_specified')
    cogzyme_short_name = request.session.get('cogzyme_short_name')
    
    ## Determine whether COG is already specified
    if not cog_specified:
        ## Is cog already specified?
        cog_specified = request.session.get('cog_specified')
        if not cog_specified:
            render_to_response('cog_unselected.html')
    
    ## Is specified value valid?
    try:
        cog = Cog.objects.get(name=cog_specified)
        request.session['cog_specified'] = cog_specified
    except:
        return render_to_response('cog_not_found.html', {'cog_specified': cog_specified})    
    
    cogzyme_table = Cogzyme.objects\
        .filter(cogs=cog)\
        .values('name')
    
    gene_table = Gene.objects\
        .filter(cogs=cog, organism__source__isnull = False)\
        .values('locus_tag','organism__taxonomy_id')
        
    
    return render_to_response('cog.html', {
        'model_specified': model_specified,
        'cog_specified': cog_specified,
        'cogzyme_specified': cogzyme_specified,
        'cogzyme_short_name': cogzyme_short_name,
        'cogzyme_table': cogzyme_table,
        'gene_table': gene_table
    })
