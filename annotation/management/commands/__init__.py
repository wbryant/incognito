rem_list = "[\-\'\s\(\)\,\[\]\.]*"

import re
from copy import deepcopy

def format_names(original_names, full_list = False):
    # Convert imported names into consistent format for comparison
    # If full_list == True, return full redundant list of names
    names = deepcopy(original_names)
    out_names = []
    #print names
    string = 0
    if type(names) is str:
        names = [names]
        string = 1
    for name in names:
        #print " - %s " % name
        name = name.lower()
        name = re.sub('\[[pemcrnxvg]\]','',name)
        minus_at_end = 0
        if re.search('-$', name):
            minus_at_end = 1
        name = re.sub(rem_list, '', name)
        if minus_at_end == 1:
            name = name + ('-')
        #print " - %s " % name
        out_names.append(name)
    #print out_names
    
    if full_list == False:
        #Remove duplicates, retaining the first name in the first position
        first_name = out_names[0]
        out_names = list(set(out_names))
        out_names_nr = []
        out_names_nr.append(first_name)
        for name in out_names:
            if name not in out_names_nr:
                out_names_nr.append(name)
        names_out = out_names_nr
    else:
        names_out = out_names
    
    if string == 1:
        names_out = names_out[0]
    #print out_names_nr
    return names_out
      