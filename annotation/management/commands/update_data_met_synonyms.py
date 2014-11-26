from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter
from myutils.django.utils import get_model_dictionary

class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        ## Cycle through command line arguments
        source_name = args[0]
        try:
            source = Source.objects.get(name = source_name)
        except:
            print("Source not found.")
        
        
        in_file = '/Users/wbryant/work/BTH/data/metanetx/chem_xref.csv'
        
        
        f_in = open(in_file, 'r')
        
        ## Get complete list of synonyms
        
        db_synonyms = Metabolite_synonym.objects.all().values_list('synonym',flat=True)
        mnxid_met_dict = get_model_dictionary(Metabolite, 'id')
        
        num_source = 0
        for line in f_in:
            if re.match(source_name + "\:",line):
                num_source += 1
        f_in.close()
        f_in = open(in_file, 'r')
        
        print("Number of lines = {}".format(num_source))
        
        counter = loop_counter(num_source, "{} lines finished".format(source_name))
        
        line_no = 0
        for line in f_in:
            if not line.startswith("#"):
                if re.match(source_name + "\:",line):
                    line_no += 1
                    print line_no
                    counter.step()
                    line_entries = line.split("\t")
                    
                    ## Find all metabolite synonyms on line and MNX ID
                    
                    mnx_id = line_entries[1]
                    
                    synonyms = []
                    synonyms.append(line_entries[0].split(":")[1])
                    for syn in line_entries[3].split("|"):
                        synonyms.append(syn)
                    
                    for syn in synonyms:
                        syn = syn.lower()
                        if syn not in db_synonyms:
#                             print syn, mnx_id
                            met_syn = Metabolite_synonym(
                                synonym = syn,
                                metabolite = mnxid_met_dict[mnx_id],
                                source = source
                            )
                            met_syn.save()
                    
#                     compact_synonyms = []
                    for syn in synonyms:
                        new_syn = syn.lower()
                        new_syn = re.sub("[^a-zA-Z0-9]+","",new_syn)
#                         compact_synonyms.append(new_syn)
                        if new_syn not in db_synonyms:
#                             print 'Compact synonym:', new_syn, mnx_id
                            met_syn = Metabolite_synonym(
                                synonym = new_syn,
                                metabolite = mnxid_met_dict[mnx_id],
                                source = source
                            )
                            met_syn.save()
        counter.stop()
                    
                    
                    
                      
            
                    