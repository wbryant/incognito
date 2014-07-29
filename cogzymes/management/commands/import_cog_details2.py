from django.core.management.base import BaseCommand, NoArgsCommand, CommandError
from cogzymes.models import *
from myutils.general.gene_parser import gene_parser
from myutils.general.utils import loop_counter
from myutils.django.utils import get_model_dictionary
import sys, re
from glob import glob
from time import time

class Command(BaseCommand):
    
    help = "Take COG/NOG details and fill COG, Gene and Organism (ID only for organism)."
     
    def handle(self, *args, **options):
        
        print "Start"
        
        cog_file_list = None
        
        try:
            start_line = int(args[0])
            args = args[1:]
        except:
            start_line = 0
        
        try:
            lines_to_read = int(args[0])
            args = args[1:]
        except:
            lines_to_read = 10000000
        
        if len(args) > 0:
            cog_file_list = []
            for arg in args:
                cog_file_list.append(arg)
        
        
        #cog_files = cog_file_list or ["/Users/wbryant/work/cogzymes/eggNOG_data/COG.members.v3.txt","/Users/wbryant/work/cogzymes/eggNOG_data/NOG.members.v3.txt"]
        
        cog_file = "/Users/wbryant/work/cogzymes/eggNOG_data/NOG.members.v3.txt"
        
        #print "Deleting old data ..."
        
        ## Delete old data from tables
        
        #Cog.objects.all().delete()
        #Gene.objects.all().delete()
        #Organism.objects.all().delete()
        
        print 'Populating Organism, Cog and Gene tables ...'
        
        time0 = time()

        cogs_present = get_model_dictionary(Cog,'name')
        organisms_present = get_model_dictionary(Organism,'taxonomy_id')
        genes_present = get_model_dictionary(Gene, ['locus_tag','organism'])
        
        lines_read = 0
         
        f_in = open(cog_file, 'r')
    
        num_lines = 0
        for line in f_in:
            num_lines += 1
            
        #print("Total number of lines in file: %d." % num_lines)
        
        num_lines = num_lines-start_line    
        
        f_in.close()
        
        f_in = open(cog_file, 'r')
        
        ### Take in all data from COG/NOG files, and 
        ### populate DB with complete set of COG/gene/organism relationships 
        
        counter = loop_counter(num_lines, "Importing COG details ...")
        
        
        for i in range(0,start_line-1):
            f_in.readline()

        for line in f_in:
            
            counter.step()
            
            ## Import data from file
            
            lines_read += 1
            if lines_read > lines_to_read:
                break
            
            cols = line.split("\t")
            cog_name = cols[0]
            org_tax_id, gene_locus = cols[1].split(".",1)
            
            if cog_name not in cogs_present:
                cog = Cog(
                    name = cog_name
                )
                cog.save()
                cogs_present[cog_name] = cog
            else:
                cog = cogs_present[cog_name]
            
            if org_tax_id not in organisms_present:
                organism = Organism(
                    taxonomy_id = org_tax_id
                )
                organism.save()
                organisms_present[org_tax_id] = organism
            else:
                organism = organisms_present[org_tax_id]
            
            if (gene_locus, organism) not in genes_present:
                gene = Gene(
                    locus_tag = gene_locus,
                    organism = organism
                )
                try:
                    gene.save()
                    genes_present[(gene_locus, organism)] = gene    
                except:
                    print cog
                    print organism
                    print gene
                    print gene_locus
                    print org_tax_id
                    print("{} - {}".format(counter.num_done, line))
            else:
                #print("Gene with locus tag '%s' (organism ID: %s) already inputted." % (gene_locus, org_id))
                gene = genes_present[(gene_locus, organism)]
            
            gene.cogs.add(cog)
            
            #num_cogs = gene.cogs.count()
            
            #if num_cogs > 1:
        
            
        counter.stop()
        
        time1 = time()
        
        print("time = {}".format(time1-time0))
        
        tot_lines_read = lines_read + start_line - 1
        
        print("Restart from line number %d." % tot_lines_read)
        
        f_in.close()
