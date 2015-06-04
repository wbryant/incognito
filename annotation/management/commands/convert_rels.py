from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from annotation.models import *
import sys, os, re
from myutils.general.utils import loop_counter, count_lines, dict_append
from abcsmc_dev.local_gene_parser import gene_parser
import abcsmc_dev.abcsmc as ada

class Command(BaseCommand):
    
    help = 'Import file and convert the relevant column from generic reaction IDs to IDs from a specific DB.'  
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        target_db='seed'
        alt_target_db='bigg'
        target_id_format='^rxn[0-9]{5}$'
        id_column = 1
        model_file='/Users/wbryant/work/MTU/gene_essentiality/abc-smc/data_files_corrected/model.xml'
        input_rels='/Users/wbryant/work/MTU/gene_essentiality/REL_lists/SEED_ICG_rels.csv'
        output_rels='/Users/wbryant/work/MTU/gene_essentiality/REL_lists/SEED_ICG_rels_seed_ids.csv'
        
#         model_file='/Users/wbryant/git/incognito/static/models/MTU_SEED_original.xml'
#         input_rels='/Users/wbryant/work/MTU/gene_essentiality/REL_lists/SEED_rels2.csv'
#         output_rels='/Users/wbryant/work/MTU/gene_essentiality/REL_lists/SEED_rels_seed_ids.csv'
        
                                    
        print("Extracting RELs from model ...")
        model = ada.create_extended_model(model_file)
        f_out = open(input_rels, 'w')
        for reaction in model.reactions:
            for enzyme in gene_parser(reaction.gene_reaction_rule):
                f_out.write("{}\t{}\n".format(
                    reaction.id,
                    enzyme))
        f_out.close()
        
        f_in = open(input_rels, 'r')
        f_out = open(output_rels, 'w')
        num_lines = count_lines(input_rels)

        print("Getting all model reaction IDs for conversion ...")
        ## Get ALL reaction IDs
        all_reaction_ids_full = []
        all_reaction_ids = []
        for line in f_in:
            line_cols = line.strip().split('\t')
            all_reaction_ids_full.append(line_cols[id_column-1])
        all_reaction_ids_full = list(set(all_reaction_ids_full))
        print("Removing '_enz' tags ...")
        for rxn_id in all_reaction_ids_full:
            rxn_id = re.sub("_enz\d+$","",rxn_id)
            all_reaction_ids.append(rxn_id)
        print ("{} IDs found.\n".format(len(all_reaction_ids)))
        f_in.close()
        
        alt_dict = {}
        alt_rxnid_list = list(Reaction_synonym.objects\
            .filter(reaction__reaction_synonym__synonym__in=all_reaction_ids,\
                    source__name=alt_target_db)\
            .distinct()\
            .values_list("reaction__reaction_synonym__synonym", "synonym"))        
        
        alt_rxnid_list2 = list(Reaction_synonym.objects\
            .filter(reaction__name__in=all_reaction_ids,
                    source__name=alt_target_db)\
            .distinct()\
            .values_list("reaction__name", "synonym"))        
        
        alt_rxnid_list.extend(alt_rxnid_list2)
        
        alt_rxnid_list = list(set(alt_rxnid_list))
        
        ## Just take first alternative ID for each reaction
        for item in alt_rxnid_list:
            if item[0] not in alt_dict:
                alt_dict[item[0]] = item[1] 
        
        
        print("Finding all SEED synonyms for these reaction IDs ...")
        f_in = open(input_rels, 'r')
        ## Create appended dictionary of reaction ID/synonym pairs    
        rxnid_synonym_list =  Reaction_synonym.objects\
            .filter(reaction__reaction_synonym__synonym__in=all_reaction_ids,
                    source__name=target_db)\
            .values('synonym','reaction__reaction_synonym__synonym')
        rxnid_synonym_dict = {}
        print("Adding all synonyms to synonym DB ...")
        for item in rxnid_synonym_list:
            dict_append(rxnid_synonym_dict, item['reaction__reaction_synonym__synonym'],item['synonym'])
        print("Adding Reaction names to synonym DB ...")
        rxnid_mnxid_list = Reaction_synonym.objects\
            .filter(reaction__name__in=all_reaction_ids,
                    source__name=target_db)\
            .values("synonym","reaction__name")
        for item in rxnid_mnxid_list:
            dict_append(rxnid_synonym_dict, item["reaction__name"],item["synonym"])
        for key, values_list in rxnid_synonym_dict.iteritems():
            rxnid_synonym_dict[key] = list(set(values_list))
        
        print("Converting IDs ...")
        
        counter = loop_counter(num_lines, "Converting IDs to {} ('{}')".format(
                                                        target_db,
                                                        target_id_format))
        rxn_ids_not_found = []
        num_converted = 0       
        num_converted_alt = 0
        for line in f_in:
            line_cols = line.strip().split('\t')
            rxn_id = line_cols[id_column-1]
            new_rxn_id = re.sub("_enz\d+$","",rxn_id)
            new_rxn_id = re.sub("_novel$","",new_rxn_id)
            if not re.match(target_id_format, new_rxn_id):
                if new_rxn_id in rxnid_synonym_dict: 
                    for item in rxnid_synonym_dict[new_rxn_id]:
                        if re.match(target_id_format,item):
                            new_rxn_id = item
                            num_converted += 1
                            break
                else:
                    if new_rxn_id in alt_dict:
                        new_rxn_id = alt_dict[new_rxn_id]
                        num_converted_alt += 1
                    else:
                        rxn_ids_not_found.append(new_rxn_id)       
            line_cols[id_column-1] = new_rxn_id
            f_out.write("{}\n".format("\t".join(line_cols)))
            counter.step()
        f_in.close()
        f_out.close()
        counter.stop()
        rxn_ids_not_found = list(set(rxn_ids_not_found))
        print("{} reaction IDs were successfully converted to target DB IDs.".format(num_converted))
        print("{} reaction IDs were successfully converted to alternative target DB IDs.".format(num_converted_alt))
        print("The following reaction IDs did not have corresponding SEED IDs or were not present in the database:\n")
        for rxn_id in rxn_ids_not_found:                
            print("'{}'".format(rxn_id))
                    