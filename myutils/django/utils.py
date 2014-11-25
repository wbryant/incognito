from myutils.general.utils import loop_counter
from django.db.models.loading import get_model
import sys

def get_model_dictionary(Model, key_columns, db = 'default'):
    """
    Create a dictionary of model entries, with key_columns as key.
    """
    
#     Model = get_model(app_name, model_name)
    
    models = Model.objects.using(db).all()
    
    model_dict = {}
    
    multi_column = False
    
    if type(key_columns) is list:
        key_string = ",".join(key_columns)
        multi_column = True
    else:
        key_string = key_columns
    
    
    counter = loop_counter(models.count(), "Creating dictionary of {}s with '{}' as key ...".format(Model.__name__, key_string))
    
    for model in models:
        counter.step()
        
        if multi_column:
            key_list = []
            for key_str in key_columns:
                key_list.append(getattr(model, key_str))
            dict_key = tuple(key_list)
#             print model.id
#             print dict_key
#             print("")
        else:
            dict_key = getattr(model, key_string)
        
        try:
            model_dict[dict_key] = model
        except:
            print("Invalid key column ...")
            sys.exit(1)
    
    counter.stop()
    
    return model_dict