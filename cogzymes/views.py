# Create your views here.

from django.shortcuts import render_to_response
from annotation.models import Model_reaction, Source, Model_metabolite
from cogzymes.models import Reaction_pred

def model_contents(request):
    
    model_data = []
    for model in Source.objects.filter(organism__isnull = False):
        model_dict = {}
        model_dict['model_id'] = model.name
        model_dict['tax_id'] = model.organism.taxonomy_id
        model_dict['Number_of_Reactions'] = Model_reaction.objects.filter(source=model).count()
        model_dict['Number_of_Metabolites'] = Model_metabolite.objects.filter(source=model).count()
        model_dict['Number_of_Predictions'] = Reaction_pred.objects.filter(dev_model=model).count()
        model_data.append(model_dict)
        print("{}, {}, {}".format(
            model_data[-1]['model_id'],
            model_data[-1]['tax_id'],
            model_data[-1]['Number_of_Predictions']
        ))
        
    if len(model_data) == 0:
        model_data = None
    
    return render_to_response('model_contents.html', {'model_data': model_data})
    

def model(request, model_id = None):
    
    if model_id:
        try:
            model_source = Source.objects.get(id=model_id)
        except:
            return render_to_response('model_not_found.html')
    
    return render_to_response('model.html', {'model_source': model_source})