from django.core.management.base import BaseCommand, NoArgsCommand, CommandError
from cogzymes.models import *
from myutils.general.gene_parser import gene_parser
from myutils.general.utils import loop_counter
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
            lines_to_read = 100000
        
        if len(args) > 0:
            cog_file_list = []
            for arg in args:
                cog_file_list.append(arg)
        
        
        cog_files = cog_file_list or ["/Users/wbryant/work/cogzymes/eggNOG_data/COG.members.v3.txt","/Users/wbryant/work/cogzymes/eggNOG_data/NOG.members.v3.txt"]
        
        #print "Deleting old data ..."
        
        ## Delete old data from tables
        
        #Cog.objects.all().delete()
        #Gene.objects.all().delete()
        #Organism.objects.all().delete()
        
        print 'Populating Organism, Cog and Gene tables ...'
            
        for cog_file in cog_files: 
            f_in = open(cog_file, 'r')
        
            num_lines = 0
            for line in f_in:
                num_lines += 1
                
            print("Total number of lines in file: %d." % num_lines)
            
            num_lines = num_lines-start_line    
            
            f_in.close()
            
            f_in = open(cog_file, 'r')
            
            ### Take in all data from COG/NOG files, and 
            ### populate DB with complete set of COG/gene/organism relationships 
            
            for i in range(0,start_line-1):
                f_in.readline()
            lines_read = 0
            
            time0 = time()
            
            counter = loop_counter(lines_to_read, "Beginning import of COG details ...")
            
            
            for line in f_in:
                
                counter.step()
                
                ## Import data from file
                
                lines_read += 1
                if lines_read > lines_to_read:
                    break
                
                cols = line.split("\t")
                cog_id = cols[0]
                org_id, gene_locus = cols[1].split(".",1)
                
                if Cog.objects.filter(id=cog_id).count() == 0:
                    cog = Cog(
                              id = cog_id
                    )
                    cog.save()
                else:
                    cog = Cog.objects.get(id=cog_id)
                
                if Organism.objects.filter(id=org_id).count() == 0:
                    organism = Organism(
                        id = org_id
                    )
                    organism.save()
                else:
                    organism = Organism.objects.get(id=org_id)
                
                if Gene.objects.filter(locus_tag=gene_locus,organism=organism).count() == 0:
                    gene = Gene(
                        locus_tag = gene_locus,
                        organism = organism
                    )
                    try:
                        gene.save()
                    except:
                        print("{} - {}".format(counter.num_done, line))
                else:
                    #print("Gene with locus tag '%s' (organism ID: %s) already inputted." % (gene_locus, org_id))
                    gene = Gene.objects.get(locus_tag=gene_locus,organism=organism)
                
                gene.cogs.add(cog)
                
                #num_cogs = gene.cogs.count()
                
                #if num_cogs > 1:

        counter.stop()
        
        
        tot_lines_read = lines_read + start_line - 1
        
        print("Restart from line number %d." % tot_lines_read)
        
        f_in.close()
