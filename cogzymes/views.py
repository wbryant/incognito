# Create your views here.

from django.shortcuts import render_to_response
from annotation.models import Model_reaction, Source, Model_metabolite

def model_contents(request):
    return render_to_response('model_contents.html')

def model(request, model_id = None):
    
    if model_id:
        try:
            model_source = Source.objects.get(id=model_id)
        except:
            return render_to_response('model_not_found.html')
    
    return render_to_response('model.html', {'model_source': model_source})