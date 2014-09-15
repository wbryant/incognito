'''
Created on 15 Sep 2014

@author: wbryant
'''

from myutils.general.utils import loop_counter
from django.db.models.loading import get_model
import sys

def write_values_list_to_tsv(values_list, out_file):
    """Take as input a values_list output from a Django query and output it to 
    a file csv file."""
    
    f_out = open(out_file, 'w')
    
    for values_entry in values_list:
        entry_list = list(values_entry)
        for idx, entry_value in enumerate(entry_list):
            if not entry_value:
                entry_list[idx] = 'None'
        
        f_out.write("{}\n".format("\t".join(entry_list)))
    
    f_out.close()
    
    