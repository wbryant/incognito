from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter

def remove_trailing_whitespaces_from_string(query_string):
    """
    Replace whitespaces at end of string
    """
    
    try:
        ws = re.findall('(\s+)$',query_string)[0]
    except:
        return None
    
    new_string = query_string.rstrip()
    
    for _ in ws:
        new_string += '\s'
    
    return new_string

def remove_trailing_whitespaces_from_synonym(synonym):
    """
    Replace whitespaces at end of synonym in DB with '\s'
    """ 
    
    new_synonym = remove_trailing_whitespaces_from_string(synonym.synonym)
    
    if new_synonym:
        synonym.synonym = new_synonym
    
    synonym.save()
    

class Command(BaseCommand):
    
    help = 'Remove whitespaces from the end of synonyms and replace with \s'
        
    def handle(self, *args, **options):
        
        """ Remove whitespaces from the end of synonyms and replace with \s
            
        """ 
        
        counter = loop_counter(Metabolite_synonym.objects.all().count(),'Replacing metabolite synonym whitespace')
        
        for synonym in Metabolite_synonym.objects.all():
            counter.step()
            remove_trailing_whitespaces_from_synonym(synonym)
        
        counter.stop()
        
        counter = loop_counter(Metabolite_synonym.objects.all().count(),'Replacing reaction synonym whitespace')
        
        for synonym in Reaction_synonym.objects.all():
            counter.step()
            remove_trailing_whitespaces_from_synonym(synonym)
        
        counter.stop()