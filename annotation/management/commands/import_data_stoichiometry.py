from django.core.management.base import BaseCommand, CommandError
from annotation.models import Reaction, Metabolite, Stoichiometry, Source
import sys, os, re


class Command(BaseCommand):
    
    help = 'Import reaction stoichiometry from MetaNetX'
        
    def handle(self, *args, **options):
        
        """ Import reaction stoichiometry from MetaNetX
            
        """ 
        
        print("Deleting previous stoichiometry ...")
        Stoichiometry.objects.all().delete()
        
        source_string = 'metanetx'
        
        if Source.objects.filter(name = source_string).count() > 0:
            met_source = Source.objects.get(name = source_string)
        else:
            met_source = Source(name = source_string)
            met_source.save()          
        
        file_in = "/Users/wbryant/work/BTH/data/metanetx/reac_prop.tsv"
        
        f_in = open(file_in, 'r')
        
        num_lines = 0
        for line in f_in:
            num_lines += 1
        f_in.close()
        f_in = open(file_in, 'r')

        
        ## Cycle through command line arguments
        num_args = 0
        for arg in args:
            num_args += 1
        
        Stoichiometry.objects.all().delete()
        
        print("Importing new stoichiometry ...")
        
        ## Initiate counter
        num_tot = num_lines
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()
        
        for line in f_in:
            if line[0] != "#":
                
                line_old = line[:]
                
                line = line.strip().split("\t")
                if len(line) > 1:
                    mnxr_id = line[0]
                    equation = line[1]
                    
#                     print mnxr_id
                    #print equation
                    
                    exact_equation = True
                    
                    try:
                        subs, prods = equation.split(" = ")
                    except:
                        print(" - %s" % line_old)
                        break

                    
                    sub_list = subs.split(" + ")
                    prod_list = prods.split(" + ")

                    
                    try:    
                        reaction = Reaction.objects.get(id = mnxr_id)
                    except:
                        #print("Reaction ID %s not found ..." % mnxr_id)  
                        reaction = Reaction(id = mnxr_id)
                        reaction.save()
                    
                    sto_entries = []
                    
                    
                    
                    for sub in sub_list:
                        try:
                            stoichiometry, m_id = sub.split(" ")
                        except:
                            exact_equation = False
                        try:
                            sto_entries.append([-1*float(stoichiometry), m_id])
                        except:
                            pass
#                             print(" - %s" % line_old)
#                             break
                        #print sto_entries[-1]
                    
                    for prod in prod_list:
                        try:
                            stoichiometry, m_id = prod.split(" ")
                        except:
                            print(" - %s" % line_old)
                            break
                        try:
                            sto_entries.append([float(stoichiometry), m_id])
                        except:
                            pass
#                             print(" - %s" % line_old)
#                             break
                        #print sto_entries[-1]
                        
                    if exact_equation == True:
                        for entry in sto_entries:
                            #print entry
                            sto, m_id = entry
                            #print sto
                            #print m_id
                            try:
                                metabolite = Metabolite.objects.get(id = m_id)
                            except:
                                #print("Metabolite ID %s not found ..." % m_id)
                                metabolite = Metabolite(
                                    id = m_id,
                                    name = m_id,
                                    source = met_source
                                )
                                metabolite.save()
                            
                            stoichiometry = Stoichiometry(
                                reaction = reaction,
                                metabolite = metabolite,
                                source = met_source,
                                stoichiometry = sto
                            ) 
                            stoichiometry.save()
                            
                        
                    
        
            ## Counter
            num_done += 1
            if ((100 * num_done) / num_tot) > next_progress:
                sys.stdout.write("\r - %d %%" % next_progress)
                sys.stdout.flush()
                next_progress += 1
                
        ## Finish counter
        sys.stdout.write("\r - 100 %\n")
        sys.stdout.flush()
                
                
                