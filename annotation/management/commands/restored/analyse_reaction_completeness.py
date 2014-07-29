from django.core.management.base import BaseCommand, CommandError
from annotation.models import Reaction, Stoichiometry, Metabolite, Compartment, Metabolite_synonym
import sys, os, re
from myutils.general.utils import loop_counter, dict_append
from libsbml import SBMLDocument, writeSBMLToFile, SBMLReader


def get_species_id_list(model_file = '/Users/wbryant/work/BTH/data/iAH991/BTH_with_gprs.xml'):
    """ Return a list of species IDs from the input model."""
    
    reader = SBMLReader()
    document = reader.readSBMLFromFile(model_file)
    model = document.getModel()
    
    species_id_list = []
    for metabolite in model.getListOfSpecies():
        species_id_list.append((metabolite.getId(), metabolite.getName()))
    
    return species_id_list

def get_sto_details(met_sto):
    """Take stoichiometry entry and return details of the metabolite."""
    
    metabolite = met_sto.metabolite
    met_details = {}
    
    ## Get metabolite compartment 
    try:
        mnx_compartment = met_sto.compartment.values_list('id', flat=True)
    except:
        mnx_compartment = '' 
    if mnx_compartment == 'MNXC2':
        met_compartment = 'e'
    else:
        met_compartment = 'c'
    
    ## Is metabolite in SEED?
    try:
        met_id_list = Metabolite_synonym.objects\
            .filter(metabolite=metabolite, source__name='seed')\
            .values_list('synonym', flat=True)
        met_id = min(met_id_list, key=len)
        met_details['seed'] = True
    except:
        met_details['seed'] = False
        met_id = metabolite.id
    
    full_met_id = 'M_' + met_id + '_' + met_compartment
    
    met_details['id'] = full_met_id
    met_details['id_short'] = met_id
    
    if met_sto.stoichiometry < 0:
        met_details['subprod'] = 's'
    elif met_sto.stoichiometry > 0:
        met_details['subprod'] = 'p'
    else:
        print("Metabolite '%s' did not have valid stoichiometry ..." % (full_met_id))
        met_details['subprod'] = 'u'
    
    return met_details
    
    

def get_reaction_seed_mets(mnxr_id):
    """Take a single reaction and return a dictionary of subs/prod either in seed/in db."""
    
    ###! Ignore subprod for now.
    
    met_list = []
    
    ## Get relevant reaction data - ID and name
    try:
        reaction = Reaction.objects.get(name=mnxr_id)
    except:
        print("Single reaction not found ...")
        sys.exit(1)
    
    stoichiometry = Stoichiometry.objects.filter(reaction=reaction)
    
    for met_sto in stoichiometry:
        met_details = get_sto_details(met_sto)    
        met_list.append(met_details)
        
    return met_list


def get_model_mets_db(model_file):
    """Take model file metabolites and try to identify in DB.
    
    This function returns a list of unambiguously mapped metabolites, in list.
    """
    
    model_mets = []     
    in_model_metabolites = get_species_id_list(model_file)
        
    num_single = 0
    num_multi = 0
    num_named = 0
    
    
    synonym_dict = {}
    source_dict = {}
    met_syns = Metabolite_synonym.objects.all().values_list('synonym','metabolite__id','source__name')
    
    
    print("Gathering raw synonyms ...")
    counter = loop_counter(len(met_syns))
    amb_met_id = "#N/A"
    for syn in met_syns:
        
        
        counter.step()
        
        synonym_raw = syn[0].lower().strip()
        if synonym_raw == amb_met_id:
            print("{}: {} ({}) - raw ...".format(synonym_raw, syn[1], syn[2]))
    
        source = syn[2]
        reaction = syn[1]
        
        #print synonym_raw
        
        ## Append raw synonyms, unless seed alternatives available
        if synonym_raw in synonym_dict:
            
            #print synonym_raw
            
            if source == 'seed':
                
                if source_dict[synonym_raw] == 'seed':
                    ## Previous synonyms are from SEED, so append
                    dict_append(synonym_dict, synonym_raw, reaction)
                else:
                    ## New synonym is from SEED so replace reactions from other sources
                    synonym_dict[synonym_raw] = [reaction]
                    source_dict[synonym_raw] = 'seed'
                    
            elif source_dict[synonym_raw] != 'seed':
                ## Append anyway
                dict_append(synonym_dict, synonym_raw, reaction)
        
        else:
            ## Create new entry
            
            #print("new met with source: {} ({})".format(synonym_raw, source))
            
            synonym_dict[synonym_raw] = [reaction]
            source_dict[synonym_raw] = source
    
    counter.stop()
    
    
    print("Gathering alternative synonyms ...")
    counter = loop_counter(len(met_syns))
    for syn in met_syns:   
         
        counter.step()
         
        ## Remove bracketed ends of synonyms 
        synonym_no_brackets = re.sub("\([^\)]*\)$","",synonym_raw)
        if synonym_no_brackets not in synonym_dict:
            dict_append(synonym_dict, synonym_no_brackets, syn[1])
            if synonym_no_brackets == amb_met_id:
                print("{}: {} ({}) - no brackets ...".format(synonym_no_brackets, syn[1], syn[2]))
    
         
        ## Remove hyphens
        synonym_no_hyphens = re.sub("-","",synonym_raw)
        if synonym_no_hyphens not in synonym_dict:
            dict_append(synonym_dict, synonym_no_hyphens, syn[1])
         
         
        ## Remove hyphens and bracketed bits
        synonym_no_hyphens_or_brackets = re.sub("-","",synonym_no_brackets)
        if synonym_no_hyphens_or_brackets not in synonym_dict:
            dict_append(synonym_dict, synonym_no_hyphens_or_brackets, syn[1])
         
    for key in synonym_dict:
        synonym_dict[key] = list(set(synonym_dict[key]))    
    counter.stop()
    
    
    
    
    print("Finding metabolites ...")
    counter = loop_counter(len(in_model_metabolites))
    unfound = []
    multi_list = []      
    for met in in_model_metabolites:
        counter.step()
        
        met_seed_id = met[0][2:-2].lower().strip()
        met_name = met[1].lower().strip()
        
        if met_seed_id in synonym_dict:
            if len(synonym_dict[met_seed_id]) > 1:
                num_multi += 1
                multi_list.append([met_seed_id,synonym_dict[met_seed_id]])
            else:
                model_mets.append(synonym_dict[met_seed_id][0])
                num_single += 1
        elif met_name in synonym_dict:
            num_named += 1
            if len(synonym_dict[met_name]) > 1:
                num_multi += 1
                multi_list.append([met_name,synonym_dict[met_name]])
            else:
                num_single += 1
                model_mets.append(synonym_dict[met_name][0])
        else:
            unfound.append((met_seed_id, met_name))
        
    counter.stop()
    
    #print model_mets
    
    model_mets = list(set(model_mets))
    
    print("{} metabolites found (unambiguous).".format(len(model_mets)))
    
    return model_mets
    
    #         for uf in unfound:
    #             print uf
    
#     print("{} out of {} metabolites unambiguously in DB.".format(num_single, len(in_model_metabolites)))
#     print("{} out of {} metabolites ambiguously in DB.".format(num_multi, len(in_model_metabolites)))
#     print("{} out of {} metabolites found by name.".format(num_named, len(in_model_metabolites)))
#     
#     print("Ambiguous metabolites:")
#     for multi in multi_list:
#         print multi

                           
class Command(BaseCommand):
    
    help = 'Take a set of reactions from the DB and create a table detailing compatibility with SEED.'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        model_file = '/Users/wbryant/work/BTH/data/iAH991/BTH_with_gprs.xml'
        
        
        ## Get list of metabolites in the model that are identified in the db
        model_mets = get_model_mets_db(model_file)
        
        
        ## Select all relevant reactions
        
        #Eficaz predictions
        rxn_list = list(Reaction.objects.filter(eficaz_prediction__total_score__gte = 0.5)
                            .order_by('name')
                            .values_list('name',flat=True))

        #Profunc predictions
        rxn_list += list(Reaction.objects.filter(profunc_prediction__total_score__gte = 0.05)
                            .order_by('name')
                            .values_list('name',flat=True))
        
        
        
        all_sp_list = []
         
        ## Dictionary to list reaction / model presence
        species_dict = {}
           
         
        
        reaction_log = []
        reaction_details = []
          
        for rxn_id in rxn_list:
            num_model = 0
            num_not_model = 0
            if rxn_id not in reaction_log:
                ## Reaction has not been tested
                
                
                reaction_log.append(rxn_id)
                rxn_mets = []
                  
                mets_details = get_reaction_seed_mets(rxn_id)
                for met in mets_details:
                    
                    met_id = met['id_short']
                    
                    ## Is metabolite in model?
                    if met_id in model_mets:
                        num_model += 1
                    else:
                        num_not_model += 1
                    
                    ## Add note of metabolite/reaction pair to species dictionary 
                    dict_append(species_dict, met['id_short'], rxn_id)
                    rxn_mets.append(met['id_short'])
                      
                    
                ## Note down relevant species details
                reaction_details.append((rxn_id, rxn_mets, num_model, num_not_model))
                  
        
        ## Now all reactions have been looked through, look for orphans
        reaction_table = []
        for rxn in reaction_details:
            orphans = 0  
            for met in rxn[1]:
                met_presence = species_dict[met]
                if len(met_presence) == 1:
                    orphans += 1
                      
                  
            reaction_row = list(rxn)
            reaction_row.append(orphans)
              
            reaction_table.append(reaction_row)
          
        print("{:>15}\t{:^10}\t{:^10}\t{:^10}".format("Reaction","Model","Non-model","Orphans"))
        for row in reaction_table:
            print("{:>15}\t{:^10}\t{:^10}\t{:^10}".format(row[0],row[2], row[3], row[4]))
              
      
    