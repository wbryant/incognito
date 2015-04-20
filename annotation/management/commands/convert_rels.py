from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter, count_lines


class Command(BaseCommand):
    
    help = 'Import file and convert the relevant column from generic reaction IDs to IDs from a specific DB.'  
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        target_db='seed'
        target_id_format='^rxn[0-9]{5}$'
        id_column = 1
        input_file='/Users/wbryant/work/MTU/gene_essentiality/REL_lists/iNJ661_rels.csv'
        output_file='/Users/wbryant/work/MTU/gene_essentiality/REL_lists/iNJ661_rels_seed_ids.csv'
        
        f_in = open(input_file, 'r')
        f_out = open(output_file, 'w')
        num_lines = count_lines(input_file)
        counter = loop_counter(num_lines, "Converting IDs to {} ('{}')".format(
                                                        target_db,
                                                        target_id_format))
        for line in f_in:
            line_cols = line.strip().split('\t')
            reaction_id = line_cols[id_column-1]
            for item in Reaction_synonym.objects.filter(reaction__reaction_synonym__synonym=reaction_id).values('synonym','source'):
                if item['source'] == target_db:
                    if re.match(target_id_format,item['synonym']):
                        reaction_id = item['synonym']
                        break
            line_cols[id_column-1] = reaction_id
            f_out.write("{}\n".format("\t".join(line_cols)))
            counter.step()
        f_in.close()
        f_out.close()
        counter.stop()
        
                    