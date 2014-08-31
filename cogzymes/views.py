# Create your views here.

from django.shortcuts import render_to_response
from annotation.models import Model_reaction, Source, Model_metabolite, Reaction_group
from cogzymes.models import Reaction_pred
from django.db.models import Count

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
    prediction_data = Reaction_pred.objects.filter(dev_model=source)
    
    return render_to_response('model.html', {                                  
        'model_rxns_data': model_rxns_data,
        'model_specified': model_specified,
        'prediction_data': prediction_data
    })
    
#     return render_to_response('model.html', {
#         'source': source, 
#         'model_rxns': model_reactions, 
#         'pred_rxns': reaction_preds,
#         'rxn_equivalents': rxn_equivalents
#     })

def model_unselected(request):
    return render_to_response('model_unselected.html')