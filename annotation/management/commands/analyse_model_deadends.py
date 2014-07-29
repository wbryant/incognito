from django.core.management.base import BaseCommand, CommandError
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter, invert_list_dict
from myutils.SBML.import_SBML import import_SBML_to_bipartite as import_SBML
from annotation.management.commands.export_db_rxns_to_model import get_species_id_dict, get_met_synonyms_db
from libsbml import SBMLDocument, writeSBMLToFile, SBMLReader

def get_species_id_dict_rev(model_file = '/Users/wbryant/work/BTH/data/iAH991/BTH_with_gprs.xml'):
    """ Return a dictionary of species ID to ID list from the input model."""
    
    reader = SBMLReader()
    document = reader.readSBMLFromFile(model_file)
    model = document.getModel()
    
    species_id_dict = {}
    ambiguous_synonyms = []
    covered_metabolites = []
    for metabolite in model.getListOfSpecies():
        
        metabolite_id = metabolite.getId()
        
        #print metabolite_id
        
        
        if metabolite_id[0:2] == "M_":
            met_id = metabolite_id[2:].lower().strip()
        else:
            met_id = metabolite_id.lower().strip()
        met_name = metabolite.getName().lower().strip()
        
        if met_id in species_id_dict:
            print("Ambiguous ID: {} - {} ({})".format(met_id, met_name, species_id_dict[met_id]))
            ambiguous_synonyms.append(met_id)
        else:
            species_id_dict[metabolite_id] = [met_id]
            
        if met_name in species_id_dict:
            if met_name != met_id:
                print("Ambiguous name: {} - {} ({})".format(met_name, met_id, species_id_dict[met_id]))
                ambiguous_synonyms.append(met_name)
        else:
            species_id_dict[metabolite_id].append(met_name + metabolite_id[-2:])
        
    for ambiguous_synonym in ambiguous_synonyms:
        species_id_dict.pop(ambiguous_synonym, None)
    
    for key in species_id_dict:
        species_id_dict[key] = list(set(species_id_dict[key]))
        
    return species_id_dict


class Command(BaseCommand):
    
    help = 'COMMAND BRIEF'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        ## Import model
        
        model_file = "/Users/wbryant/work/BTH/analysis/working_models/iah_epz.xml"
        G = import_SBML(model_file)
        
        ## For all metabolites, try to find DB metabolite
        
        model_dict = get_species_id_dict_rev(model_file)
        db_met_syn_dict = get_met_synonyms_db()
        db_syn_met_dict = invert_list_dict(db_met_syn_dict)
        
#         for idx, key in enumerate(model_dict):
#             if idx > 20:
#                 break
#             print("{:10}: {}".format(key, model_dict[key]))
#         
#         
#         for idx, key in enumerate(db_syn_met_dict):
#             if idx > 20:
#                 break
#             print("{:10}: {}".format(key, db_syn_met_dict[key]))
            
#         num_shown = 0
#         for key in db_syn_met_dict:
#             num_shown += 1
#             if num_shown > 10:
#                 break
#             print key, db_syn_met_dict[key]
        

        
        db_model_met_ids = {}
        deadend_mets = []
        mapped_mets = []
        
#         num = 0
        
        
        for idx in G.nodes():
#             num += 1
#             if num > 100:
#                 break
            node = G.node[idx]
            if node['type'] == 'metabolite':
                ### Does metabolite correspond to DB metabolite?
                
                ## Get list of IDs from model for lookup in DB
                
                model_id = node['id']
                model_ids_for_lookup = model_dict[model_id]
                
#                 print model_ids_for_lookup
                
                ## Is there an unambiguous mapping to the metabolite?
                
                db_met_id = []
                
                for model_id in model_ids_for_lookup:
                    if model_id[:-2] in db_syn_met_dict:
                        db_met_id.append(db_syn_met_dict[model_id[:-2]])
                
#                 print db_met_id
                
                db_met_id = list(set(db_met_id))
                
                if len(db_met_id) == 1:
                    db_met_id = db_met_id[0]
                    db_model_met_ids[db_met_id] = model_id
                    mapped_mets.append(db_met_id)
                else:
                    ## No unambiguous mapping
                    continue
        
            
                ## Find deadend metabolites
            
                if (G.degree(idx) == 1) and (model_id[-2:] != "_e"):
#                     print("DEM: {} - {}".format(model_id, db_met_id))
                    deadend_mets.append(db_met_id)
        
            
#         print len(mapped_mets)
#         print len(deadend_mets)
#         
#         print("Deadend mets:")
#         for met in deadend_mets:
#             print(" - {}".format(met))
        
        
        ### Find reactions in DB that contain only model metabolites
        
        ## Get list of reaction/metabolite pairs from DB
        
        reactions = Reaction.objects.all()
        
        counter = loop_counter(len(reactions), "Getting metabolite data for DB reactions ...")
        
        rxn_met_list = []
        
        for reaction in reactions:
            counter.step()
            rxn_id = reaction.name
            met_id_list = []
            met_ids = Stoichiometry.objects.filter(reaction=reaction).values_list('metabolite__id',flat=True)
            
            for met_id in met_ids:
                #print met_id
#                 if met_id in mapped_mets:
#                     print("Reaction {}: {} is present in the model ...".format(rxn_id, met_id))
#                     if met_id in deadend_mets:
#                         print(" - and is a deadend ...") 
                met_id_list.append(met_id)
            
            rxn_met_list.append((rxn_id, met_id_list))
        
        counter.stop()
        
        ## for each reaction, are all metabolites in the mapped_mets list? 
        
        num_full_reactions = 0
        num_full_with_deadends = 0
        list_full_with_deadends = []
        num_reactions = len(rxn_met_list)
        
        counter = loop_counter(len(rxn_met_list))
        
        for reaction in rxn_met_list:
            counter.step()
            rxn_id = reaction[0]
#             print("Reaction {}:".format(rxn_id))
            num_in_model = 0
            num_deadend = 0
            total = len(reaction[1])
            for metabolite in reaction[1]:
                if metabolite in mapped_mets:
                    num_in_model += 1
                    if metabolite in deadend_mets:
                        num_deadend += 1
            
            if num_in_model == total:
                num_full_reactions += 1
                if num_deadend > 1:
                    num_full_with_deadends += 1
                    list_full_with_deadends.append(reaction)
            
        counter.stop()
        
            #print(" - mets: {}, in model: {}, deadend: {}".format(total, num_in_model, num_deadend))
        
        ## - if so, are > 1 deadend metabolites?
         
        print("Number of reactions: {}".format(num_reactions))
        print("Number matching model reactions: {}".format(num_full_reactions))
        print("Number including at least 2 deadend metabolites: {}".format(num_full_with_deadends))
#         for reaction in list_full_with_deadends:
#             print(" - {} ({} metabolites)".format(reaction[0], len(reaction[1])))
        
        
        ### Search database results for evidence of these reactions
        
        for reaction in list_full_with_deadends:
            ## Try Profunc first - cannot be done by results because they do not do individual reactions, must use predictions.
            
            rxn_id = reaction[0]
            
#             ## Cogzyme predictions -- NONE PRODUCE CANDIDATES
#             genes = Cogzyme_prediction.objects.filter(reaction__name = rxn_id)\
#                                     .values_list('gpr', flat = True)\
#             
#             genes_and_scores = []                        
#             for gene in genes:
#                 genes_and_scores.append((gene, 1))
            
#             ## Profunc predictions
#             genes_and_scores = Profunc_prediction.objects.filter(reaction__name = rxn_id)\
#                                     .order_by('-profunc_score')\
#                                     .values_list('gene__locus_tag','profunc_score')\
                                    
            ## EFICAz predictions
            genes_and_scores = Eficaz_prediction.objects.filter(reaction__name = rxn_id)\
                                    .order_by('-eficaz_score')\
                                    .values_list('gene__locus_tag','eficaz_score')\
            
            if len(genes_and_scores) > 0:
                print("Predictions found for deadend-filling reaction {}:".format(rxn_id))
                for gene_and_score in genes_and_scores[:2]:
                    print(" - {} ({})".format(gene_and_score[0], gene_and_score[1]))
        
        
        ## Cycle through command line arguments
        num_args = 0
        for arg in args:
            num_args += 1
        
                    