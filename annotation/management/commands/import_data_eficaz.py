from django.core.management.base import NoArgsCommand, CommandError
from annotation.models import GO, Gene, Eficaz_result, EC
#from ffpred.extract_results import *
import sys, os, re, shelve, glob

class Command(NoArgsCommand):
    
    help = 'Imports data from EFICAz 2.5 results.'
        
    def handle(self, **options):
        
        """ Results from each EFICAz submission must be parsed and added to the database, along with their scores.
            
        """
        
        input_folder = "/Users/wbryant/work/BTH/data/eficaz/output/eficaz_results/"
        
        os.chdir(input_folder)
        
        file_list = glob.glob("*.ecpred")
        
        fail = 0
        
        for file in file_list:
            
            f_in = open(file, "r")
            
            file_lines = []
            
            for line in f_in:
                if "No EFICAz EC assignment" in line:
                    break
                else:
                    items = line.split(",")
                    
                    try:
                        gene = Gene.objects.get(protein_gi = items[0])
                    except:
                        print("Protein ID %s not found ..." % items[0])
                        gene = []
                    
                    ec_number_groups = re.search("((?:[0-9]+\.){3}[0-9]+)", items[1])
                    if ec_number_groups is None:    
                        ec_number_groups = re.search("((?:[0-9]+\.){2}[0-9]+)", items[1])
                        #print("3-digit EC!")
                        ec_number = ec_number_groups.group(1) + ".-"
                    else:
                        ec_number = ec_number_groups.group(1)
                        
                    try:
                        ec = EC.objects.get(number = ec_number)
                    except:
                        print("EC number '%s' not found ..." % ec_number)
                        ec = []
                    
                    try:
                        seq_id_bin = int(items[3][-1])
                    except:
                        print("Sequence ID bin is not integer - %s ..." % items[3][-1])
                        seq_id_bin = []
                    
                    precision = re.search("\:\s*([0-9\.]+)\;\s*([0-9\.]+)", items[4])
                    if precision is not None:
                        precision_mean = float(precision.group(1))
                        precision_sd = float(precision.group(2))
                    else:
                        #print("%s" % items[4])
                        precision_mean = 0.001
                        precision_sd = 0.001
                    
                    try:
                        eficaz_result = Eficaz_result(
                            gene = gene,
                            ec = ec,
                            precision_mean = precision_mean,
                            precision_sd = precision_sd,
                            seq_id_bin = seq_id_bin
                        )
                        eficaz_result.save()
                        #print("Result successfully saved ...")
                    except:
                        fail += 1
                        pass
                        print(" - Not saved")
        
        print fail
        