from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter

class Command(BaseCommand):
    
    help = 'Import compartment data from model file specified in argument'
        
    def handle(self, *args, **options):
        
        """ Import compartment data from model file specified in argument
            
        """ 
        ## Cycle through command line arguments
        if len(args) <> 1:
            print("Only a single argument should be passed to this command, the model file path.")
            sys.exit(1)
        else:
            file_in = args[0] 
        
        source_filename = file_in.split("/")[-1]
        
        if source_filename in Source.objects.all().values_list("name",flat=True):
            source = Source.objects.get(name=source_filename)
        else:
            source = Source(
                name=source_filename
            )
            source.save()
            
        ## Create reaction IDs list
        
        mnxrxn_id_list = Reaction.objects.all().values_list("name", flat=True)
        
#         ## Create id to reaction dictionary from Reaction and to metabolite dictionary from Metabolite
#         
#         print("Creating metabolite and reaction dictionaries ...")
#         
#         rxns = Reaction.objects.all()
#         rxn_dict = {}
#         for rxn in rxns:
#             rxn_dict[rxn.id] = rxn
#         
#         mets = Metabolite.objects.all()
#         met_dict = {}
#         for met in mets:
#             met_dict[met.id] = met
        
        ## Create Compartment dictionary
        
        print("Creating compartment and direction dictionaries ...")
        
        comps = Compartment.objects.all()
        comp_dict = {}
        for comp in comps:
            comp_dict[comp.id] = comp
    
        directions = Direction.objects.all()
        direction_dict = {}
        for direction in directions:
            direction_dict[direction.direction] = direction
        
        
        ## Count incompletely compartmentalised reactions
        
        init_num_incomplete = Reaction.objects.filter(stoichiometry__compartment__isnull=True).distinct().count()
        
        
        ## Create Stoichiometry dictionary, using reaction, metabolite and stoichiometry as 
        
        print("Creating stoichiometry dictionary ...")

        stos = Stoichiometry.objects.filter(source__name="metanetx").prefetch_related()
        sto_dict = {}
        
        loop = loop_counter(len(stos))
        
        for sto in stos:
            sto_dict[(sto.reaction.name, sto.metabolite.id, sto.stoichiometry)] = sto            
            loop.step()

        loop.stop()

                        
        f_in = open(file_in, 'r')
        num_lines = 0
        for line in f_in:
            num_lines += 1
        f_in.close()
        f_in = open(file_in, 'r')
        
#         ## Initiate counter
#         num_tot = num_lines
#         num_done = 0
#         next_progress = 1
#         sys.stdout.write("\r - %d %%" % num_done)
#         sys.stdout.flush()
        
        print("Importing stoichiometries from model file ...")
        
        for line in f_in:
            if line[0] != "#":
                line_old = line[:]
                cols = line.strip().split("\t")
                if (len(cols) >= 4):
                    if (len(cols[3]) > 0):
#                         print("Analysing reaction details ...")
                        equation = cols[1]
                        mnxrxn_id = cols[3]
                        
                        #print("- %s" % mnxrxn_id)
                        #print("- '%s'" % line_old)
                        
                        if mnxrxn_id not in mnxrxn_id_list:
#                             print("No MetaNetX reaction ID (%s), skipping ..." % mnxrxn_id)
                            continue
                        
                        
                        ## Determine reaction directionality
                        try:
                            if "-->" in equation:
                                model_direction = "ltr"
                                lhs, rhs = equation.split(" --> ")
                            elif "<--" in equation:
                                model_direction = "rtl"
                                lhs, rhs = equation.split(" <-- ")
                            elif "<==>" in equation:
                                model_direction = "both"
                                lhs, rhs = equation.split(" <==> ")
                            else:
#                                 print("Reaction did not split correctly ...")
#                                 print(" - %s" % equation)
                                continue
                        except:
#                             print("Reaction did not split correctly ...")
#                             print(" - %s" % equation)
                            continue
                        
                        ## Determine way round of reaction and correct if different from MetaNetX
                         
                        sto_met_comps = lhs.split(" + ")
                        sto_met_comp_1 = sto_met_comps.pop(0)
                        
                        try:
                            first_sto, first_met_comp = sto_met_comp_1.split(" ")
                            first_sto = -1*float(first_sto)
                            first_met, _ = first_met_comp.split("@")
                        except:
#                             print("Reaction did not conform to required format, skipping ...")
#                             print(" - %s" % equation)
                            continue
                        
                        sto_tuple = (mnxrxn_id, first_met, first_sto)
                        
                        ### Single tuple used to determine direction is not robust due to transport.  Therefore, create list of all tuples and see which way round yields the most hits and choose that
                        
                        ## Create all tuples, including reverse ones
                        sto_met_comps_lhs = lhs.split(" + ")
                        sto_met_comps_rhs = rhs.split(" + ")
                        sto_tuples_model = []
                        sto_tuples_reverse = []
                        sto_tuple_comp_dict = {}
                        for sto_met_comp in sto_met_comps_lhs:
                            sto, met_comp = sto_met_comp.split(" ")
                            sto = -1*float(sto)
                            met_id, comp_id = met_comp.split("@")
                            
                            sto_tuple = (mnxrxn_id, met_id, sto)
                            sto_tuples_model.append(sto_tuple)
                            sto_tuple_comp_dict[(sto_tuple, "model")] = comp_id
                            
                            sto_tuple = (mnxrxn_id, met_id, -1*sto)
                            sto_tuples_reverse.append(sto_tuple)
                            sto_tuple_comp_dict[(sto_tuple, "reverse")] = comp_id
                            
                        for sto_met_comp in sto_met_comps_rhs:
                            sto, met_comp = sto_met_comp.split(" ")
                            sto = float(sto)
                            met_id, comp_id = met_comp.split("@")
                            
                            sto_tuple = (mnxrxn_id, met_id, sto)
                            sto_tuples_model.append(sto_tuple)
                            sto_tuple_comp_dict[(sto_tuple, "model")] = comp_id
                            
                            sto_tuple = (mnxrxn_id, met_id, -1*sto)
                            sto_tuples_reverse.append(sto_tuple)
                            sto_tuple_comp_dict[(sto_tuple, "reverse")] = comp_id
                            
                            
                        ## Test which orientation fits best with the database
                        correct_count = 0
                        backward_count = 0
                        
                        for sto_tuple in sto_tuples_model:
                            if sto_tuple in sto_dict:
                                correct_count += 1
                                
                        for sto_tuple in sto_tuples_reverse:
                            if sto_tuple in sto_dict:
                                backward_count += 1
                        
                        if correct_count >= backward_count:
                            equation_orientation = "model"
#                             print("Order is correct ...")
                            sto_tuples = sto_tuples_model
                        else:
                            equation_orientation = "reverse"
#                             print("Order is reverse ...")
                            if model_direction != "both":
                                model_direction = model_direction[::-1]
                            sto_tuples = sto_tuples_reverse
                        
#                         print("Assigning compartments ...")
                        
                        ## Use the relevant direction to assign compartments and directionality to all metabolites and reactions respectively
                        for sto_tuple in sto_tuples:
                            try:
                                stoichiometry = sto_dict[sto_tuple]
                                
                                stoichiometry.compartment = comp_dict[sto_tuple_comp_dict[(sto_tuple, equation_orientation)]]
                                
                                stoichiometry.save()
                                
                                #stoichiometry.direction = direction_dict[model_direction]
                                
                                #stoichiometry.save()
                            except:
#                                 print("%s tuple not found, adding to DB ..." % str(sto_tuple))
                                
                                rxn = Reaction.objects.get(name=sto_tuple[0], source__name="metanetx")
                                met = Metabolite.objects.get(id=sto_tuple[1])
                                sto = sto_tuple[2]
                                try:
                                    compartment = comp_dict[sto_tuple_comp_dict[(sto_tuple, equation_orientation)]]
                                except:
                                    compartment = None
                                #direction = direction_dict[model_direction]
                                
                                if Stoichiometry.objects.filter(reaction=rxn, metabolite=met, source__name="metanetx").count() > 0:
#                                     print(" - Metabolite found in reaction, replacing with new stoichiometry ...")
                                    Stoichiometry.objects.filter(reaction=rxn, metabolite=met, source__name="metanetx").delete()
                                
                                stoichiometry = Stoichiometry(
                                    reaction=rxn,
                                    metabolite=met,
                                    source=source,
                                    compartment=compartment,
                                    #direction=direction,
                                    stoichiometry=sto
                                )
                                stoichiometry.save()
                        
#                         print("Checking completeness ...")
                        
                        ##! For each reaction affected, if there are still uncompartmentalised metabolites, print reaction
                        
                        stoichiometries = Stoichiometry.objects.filter(reaction__name=sto_tuple[0], source__name="metanetx")
                        num_stos = len(stoichiometries)
                        num_with_comps = 0
                        
                        for sto in stoichiometries:
                            if sto.compartment:
                                num_with_comps += 1
                            rxn_name = sto.reaction.name
                        
                        if num_with_comps < num_stos:
                            print("-> Reaction '%s' has incomplete compartmentalisation ..." % rxn_name)
#                         else:
#                             print("-> Reaction '%s' has complete compartmentalisation ..." % rxn_name)
        
        final_num_incomplete = Reaction.objects.filter(stoichiometry__compartment__isnull=True).distinct().count()
                  
        num_completed = init_num_incomplete - final_num_incomplete
        
        print("This model completed the compartmentalisation of %d reactions." % num_completed)           
                            
#                         if sto_tuple not in sto_dict:
#                             ## If stoichiometry as in DB then the reaction is in conventional order, else try backward order
#                             
#                             sto_tuple = (mnxrxn_id, first_met, -1*first_sto)
#                             
#                             if sto_tuple in sto_dict:
#                                 
#                                 print("- Order is opposite, switching LHS and RHS (%s) ..." % model_direction)
#                                 if model_direction != "both":
#                                     model_direction = model_direction[::-1]
#                                 swap = lhs[:]
#                                 lhs = rhs[:]
#                                 rhs = swap[:]
#                                 #print sto_tuple
#                                 
#                             else:
#                                 print("Stoichiometry not found ...")
#                                 #print(" - '%s'" % line_old)
#                                 continue
#                         else:
#                             pass
#                             print("- Order is correct (%s) ..." % model_direction)
#                             #print sto_tuple
#                             
#                         ###! TO DO: Get all tuples for each reaction and find stoichiometry.  Once found, add compartments and direction to the stoichiometries.
#                         
#                         ## LHS
#                         sto_met_comps = lhs.split(" + ")
#                         
#                         for sto_met_comp in sto_met_comps:
#                             sto, met_comp = sto_met_comp.split(" ")
#                             sto = float(sto)
#                             met_id, comp_id = met_comp.split("@")
#                             
#                             ## These are substrates, so stoichiometry will be negative
#                             
#                             sto = -1*sto
#                             
#                             try:
#                                 stoichiometry = sto_dict[(mnxrxn_id, met_id, sto)]
#                                 
#                                 stoichiometry.compartment = comp_dict[comp_id]
#                                 
#                                 stoichiometry.save()
#                                 
#                                 stoichiometry.direction = direction_dict[model_direction]
#                                 
#                                 stoichiometry.save()
#                             except:
#                                 print("LHS")
#                                 print("'%s' tuple not found ..." % str(sto_tuple))
#                                 print("- %s" % equation)
#                                 pass
#                         ## RHS
#                         sto_met_comps = rhs.split(" + ")
#                         
#                         for sto_met_comp in sto_met_comps:
#                             sto, met_comp = sto_met_comp.split(" ")
#                             sto = float(sto)
#                             met_id, comp_id = met_comp.split("@")
#                             
#                             ## These are products, so stoichiometry will be positive
#                             
#                             try:
#                                 stoichiometry = sto_dict[(mnxrxn_id, met_id, sto)]
#                                 
#                                 stoichiometry.compartment = comp_dict[comp_id]
#                                 
#                                 stoichiometry.save()
#                                 
#                                 stoichiometry.direction = direction_dict[model_direction]
#                                 
#                                 stoichiometry.save()
#                             except:
#                                 print("RHS")
#                                 print("'%s' tuple not found ..." % str(sto_tuple))
#                                 print("- %s" % equation)
#                                 pass
#                             
        
#             ## Counter
#             num_done += 1
#             if ((100 * num_done) / num_tot) > next_progress:
#                 sys.stdout.write("\r - %d %%" % next_progress)
#                 sys.stdout.flush()
#                 next_progress += 1
#                 
#         ## Finish counter
#         sys.stdout.write("\r - 100 %\n")
#         sys.stdout.flush()
                
                
                