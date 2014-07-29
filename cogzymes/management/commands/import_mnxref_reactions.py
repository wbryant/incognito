from django.core.management.base import BaseCommand, NoArgsCommand, CommandError
from cogzymes.models import *
from myutils.general.gene_parser import gene_parser
from myutils.SBML.import_SBML import import_SBML_to_bipartite as import_SBML
from myutils.SBML import calculate_stats as cas
import sys, re
from glob import glob
from time import time

def import_mnxref_dict(mnxref_file = "/Users/wbryant/work/cogzymes/data/reac_xref130614.tsv"):
    """
    Import all mapped names from MNXRef tsv file into a dictionary to try to convert any reaction names to the common MNXRef namespace.
    """
    
    f_in = open(mnxref_file, "r")
    
    ## Skip comments
    line = f_in.readline()
    while line[0] == "#":
        line = f_in.readline()
    
    mnxref_dict = {}
    mnxref_dup_dict = {}
    
    for line in f_in:
        
        r_id_tot, mnxref_id = line.strip().split("\t")
        source, r_id = r_id_tot.split(":")[0:2]
        
        if r_id in mnxref_dict:
            if mnxref_id != mnxref_dict[r_id][0]:
                print("Duplicate ID found with '%s' := '%s', original is '%s' := '%s'." % (r_id_tot, mnxref_id, mnxref_dup_dict[r_id], mnxref_dict[r_id][0]))
                mnxref_dict[r_id]  = ('duplicate','duplicate')
        else:
            mnxref_dict[r_id] = (mnxref_id,source)
            mnxref_dup_dict[r_id] = r_id_tot
    
    r_dups = []
    for r_id in mnxref_dict:
        if mnxref_dict[r_id][0] == 'duplicate':
            r_dups.append(r_id)
    for r_dup in r_dups:
        del mnxref_dict[r_dup] 
    
    return mnxref_dict

class Command(BaseCommand):
    
    help = "Import MNXRef reactions and synonyms into database."
        
    def handle(self, *args, **options):
        
        print "Start"
        
        
        if len(args) != 1:
            print("Only one argument should be provided, the MNXRef file path and name.")
            sys.exit(1)
        else:
            mnxref_filename = args[0]
            
        print("Deleting previous MNXRef data ...")
        
        Reaction.objects.all().delete()
        Reactionsynonym.objects.all().delete()
        Reactionsynonymsource.objects.all().delete()
        
        print("Importing data from MNXRef data file ...")
        
        mnxref_dict = import_mnxref_dict(mnxref_filename)
        
        for synonym in mnxref_dict:
            mnxref_id = mnxref_dict[synonym][0]
            source_name = mnxref_dict[synonym][1]
            
            try:
                reaction = Reaction.objects.get(mnx_id=mnxref_id)
            except:
                reaction = Reaction(
                    name = mnxref_id,
                    mnx_id = mnxref_id
                )
                reaction.save()
            
            source = Reactionsynonymsource(
                name = source_name
            )
            source.save()
            
            reactionsynonym = Reactionsynonym(
                synonym = synonym,
                source = source,
                reaction = reaction,
            )
            reactionsynonym.save()
            
                 