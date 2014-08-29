# Create your views here.

from django.shortcuts import render_to_response
from annotation.models import Model_reaction, Source, Model_metabolite, Reaction_group
from cogzymes.models import Reaction_pred
from django.db.models import Count

model_specified = None

def home(request):
    
    if not model_specified:
        print 'None'
    else:
        print model_specified
    
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
    

def model(request, model_id = None):
    
    if model_id:
        try:
            source = Source.objects.get(name=model_id)
            model_specified = model_id
        except:
            return render_to_response('model_not_found.html', {'model_id': model_id})
    
#     model_reactions = Model_reaction.objects.filter(source=source)
#     reaction_preds = Reaction_pred.objects.filter(dev_model=source)
#     rxn_equivalents = {}
#     for rxn in model_reactions:
#         rxn_equivalents[rxn.model_id] = Model_reaction.objects.filter(mapping__model_reaction=rxn).distinct().count()
 
    model_rxns_data = Model_reaction.objects\
        .filter(source=source)\
        .annotate(equiv_count=Count('mapping__model_reaction'))\
        .values('model_id','name','gpr','db_reaction__name','equiv_count')
    
    for rxn_data in model_rxns_data:
        rxn_data['equiv_count'] -= 1
        if rxn_data['equiv_count'] < 0:
            rxn_data['equiv_count'] = 0
    
    return render_to_response('model.html', {                                  
        'model_rxns_data': model_rxns_data,
        'model_specified': model_specified
    })
    
#     return render_to_response('model.html', {
#         'source': source, 
#         'model_rxns': model_reactions, 
#         'pred_rxns': reaction_preds,
#         'rxn_equivalents': rxn_equivalents
#     })

def model_unselected(request):
    return render_to_response('model_unselected.html')