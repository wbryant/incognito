from django.core.management.base import NoArgsCommand, CommandError
from annotation.models import GO, Gene, Profunc_result
#from ffpred.extract_results import *
import sys, os, re, shelve
from glob import glob

class Command(NoArgsCommand):
    
    help = 'Imports data from Profunc results.'
        
    def handle(self, **options):
        
        """ Results from each Profunc submission must be parsed and added to the database, along with their scores.
            
        """ 
        
        input_dir = "/Users/wbryant/work/BTH/data/profunc/results2/"
        id2prot_file = open("/Users/wbryant/work/BTH/data/profunc/results2/id_to_gi.txt","r")
        
        
        ## Get list of input files
        input_files = glob(input_dir + "*.txt")
        
#         for id in range(1,2149):
#             id_input = "%06d" % id
#             input_file = "go_terms_" + id_input + ".txt"
#             input_files.append((id_input, (input_dir + input_file)))
#                 
        ## Get ID to gene relationship for each Profunc result.
        id_to_gene_dict={}
        
        for line in id2prot_file:
            input = line.split("\t")
            id = input[0]
            prot_gi = input[1]
            try:    
                gene = Gene.objects.get(protein_gi=prot_gi)
            except:
                print("Protein GI not found: %s" % prot_gi)
                gene = Gene.objects.get(locus_tag="BT_1450")
            
            id_to_gene_dict[id] = gene
            
        
        
        print 'Populating Profunc_result table ...'
        ## Initiate counter
        num_tot = len(input_files)
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()
        
        ## Go through each file inputting the data into the database
        for file in input_files:
            
            idx = re.sub(".+_([0-9]+)\.txt","\g<1>",file)
            if idx in id_to_gene_dict:
                gene = id_to_gene_dict[idx]
                f_in = open(file, 'r')
                
                for line in f_in:
                    fields = line.split('\t')
                    
                    go_id = fields[1]
                    
                    
                    ##? Some GO terms are not found here - they are alternative IDs for other GO terms.
                    ##? No action taken now, but may require being looked at later.
                    if GO.objects.filter(id=go_id).count() > 0:
                        go = GO.objects.get(id=go_id)
                        
                        score = fields[2]
                        
                        result = Profunc_result(
                            gene = gene,
                            go_term = go,
                            score = score
                        )
                        
                        result.save()
                    #else:
                    #    print("GO term %s could not be found" % go_id)
            
            ## Counter
            num_done += 1
            if ((100 * num_done) / num_tot) > next_progress:
                sys.stdout.write("\r - %d %%" % next_progress)
                sys.stdout.flush()
                next_progress += 1
                
        ## Finish counter
        sys.stdout.write("\r - 100 %\n")
        sys.stdout.flush()
                
                
                