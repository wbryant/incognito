'''
Created on 11 Mar 2014

@author: wbryant
'''

from django.db.models import Count, F, Q, Avg, Max



import sys, os, re
from collections import OrderedDict
from myutils.django.utils import get_model_dictionary
#sys.path.append("/Users/wbryant/work/BTH/incognito")
#sys.path.append("/Users/wbryant/work/BTH/incognito/annotation")
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
#from annotation.models import Reaction, Metabolite, Stoichiometry
# from annotation.models import Reaction, Metabolite, Stoichiometry, Model_reaction

from annotation.models import Model_reaction, Source
from annotation.models import Reaction, Metabolite, Metabolite_synonym, Stoichiometry, Model_metabolite
from collections import Counter
from myutils.general.utils import loop_counter


# def find_reaction_overlaps(in_reaction, source = None):
#     """
#     For a reaction, find and print out all reactions overlapping by more than one metabolite, starting with highest overlap.
#     """
#     
#     if source is not None:
#         try:
#             in_reaction = Reaction.objects.get(name=in_reaction, source=source)
#         except:
#             print("Reaction not found ...")
#             sys.exit(1)
#     
#     ### Get list of stoichiometries for reactions sharing two or more metabolites with the reaction
#     
#     print("Reaction '%s':\n" % in_reaction.name)
#     print(" - %s\n" % in_reaction.equation())
#     
#     num_mets = Stoichiometry.objects.filter(reaction=in_reaction).count()
#     
#     overlaps_found = False
#     equivalent_rxns = True
#     
#     while not overlaps_found:
#         overlap_rxns = Reaction.objects\
#             .filter(stoichiometry__metabolite__in 
#                     = Metabolite.objects
#                         .filter(stoichiometry__reaction=in_reaction)
#                         .distinct())\
#             .annotate(num_mets_overlap=Count('id'))\
#             .distinct()\
#             .filter(num_mets_overlap=num_mets)\
#             .exclude(name=in_reaction.name)
#         
#         num_mets -= 1
#         
#         
#         if equivalent_rxns:
#             equivalent_rxns = False
#         else:
#             if (overlap_rxns.count() > 0):
#                 overlaps_found = True
#                 
#         for rxn in overlap_rxns:
#                 ## Get stoichiometry, and print out in the form of a reaction equation
#                 
#                 print("'%s': %s" % (rxn.name, rxn.equation()))
#                 

def find_model_crossover_reactions(model1_source_name, model2_source_name, Model_reaction):
    """
    Find all reactions (and metabolites LATER!!!) that can be mapped between two models.
    """
    
    model1_mapped = Model_reaction.objects.filter(source__name=model1_source_name, db_reaction__isnull=False).values_list("model_id","db_reaction__name").distinct()
    model2_mapped = Model_reaction.objects.filter(source__name=model2_source_name, db_reaction__isnull=False).values_list("model_id","db_reaction__name").distinct()
    
    ## Create dictionary from model1 ID to MNX ID
    model1_mnx_dict = {}
    for entry in model1_mapped:
        model1_mnx_dict[entry[0]] = entry[1]
    
    
    ## Create dictionary from MNX ID to model2 ID
    mnx_model2_dict = {}
    for entry in model2_mapped:
        mnx_model2_dict[entry[1]] = entry[0]
        
    
    ## Print the crossover
    for entry in model1_mnx_dict:
        mnx1 = model1_mnx_dict[entry]
        
        if mnx1 in mnx_model2_dict:
            m1_name = entry
            m2_name = mnx_model2_dict[mnx1]
            print("{}\t{}".format(m1_name,m2_name))


# def get_model_rxn_from_db_rxn(db_reaction, dev_model):
#     """
#         From a DB reaction or DB reaction name, find the corresponding reaction
#         in a particular model, return empty if none or more than one model 
#         reactions are found. 
#     """
#     



def get_dbmets_not_dev_model(dev_model, connectivity_min = 2, name_source = None):
    """
    Find all metabolites predicted to be added to the development model that 
    are not deadends in the prediction set
    """
    
    pred_rxns = Reaction.objects.filter(model_reaction__reaction_pred__dev_model=dev_model).distinct()
    
    pred_mets = Metabolite.objects\
        .filter(stoichiometry__reaction__in=pred_rxns)\
        .exclude(model_metabolite__source=dev_model)\
        .distinct()
        
    pred_mets_counts = Counter(Stoichiometry.objects
        .filter(reaction__in=pred_rxns,metabolite__in=pred_mets)
        .values_list('metabolite__name',flat=True))
    
    for met in pred_mets:
        if pred_mets_counts[met.name] > connectivity_min:
            
            ## Find name from name_source
            if name_source:
                source_synonyms = "; ".join(list(Metabolite_synonym.objects\
                    .filter(metabolite=met, source__name=name_source)\
                    .values_list('synonym', flat=True)))
            else:
                source_synonyms = ""
            
            if len(source_synonyms) != 0:
                source_synonyms  = ":\t" + source_synonyms 
            
            print met.name, source_synonyms
                
def tidy_synonym_list(syn_list, dup_warning = None, replacement_pairs = None):
    """
    Remove all non-alphanumerics, put into lower-case, remove superfluous 
    start/end characters.
    """
    #syn_list = list(set(syn_list))
    
    if dup_warning:
        non_dup_len = len(syn_list)
        
    if not replacement_pairs:
        replacement_pairs = [
            ('_[a-zA-Z]$',''),
            ('^M_',''),
            ('^R_',''),
            ('_DASH_','-'),
            ('_LPAREN_','('),
            ('_RPAREN_',')'),
            ('[^0-9a-zA-Z]+','')
        ]
    
    syn_list_repped = []
    for syn_rep in syn_list:
        for rep_pair in replacement_pairs:
            syn_rep = re.sub(rep_pair[0],rep_pair[1],syn_rep)
        syn_list_repped.append(syn_rep.lower())
    
    if dup_warning:
        non_dup_repped_len = len(set(syn_list_repped))
        if non_dup_repped_len < non_dup_len:
            num_duplications = non_dup_len - non_dup_repped_len
            print(" - {} duplications created through replacements!".format(num_duplications))
        else:
            print(" - No duplications created.")
    
    return syn_list_repped

def find_mets_in_tsv(file_in, model = 'iAH991', file_out = None):
    """
    Discover from synonyms whether metabolites named in a file are in 
    a particular model (or can be found at all in the DB).
    """
    
    if not file_out:
        file_out = re.sub('(\.[^\.]+)$','_out\g<1>',file_in)
    
    f_in = open(file_in, 'r')
    f_out = open(file_out,'w')
    
    print("Getting DB synonym list ...")
    db_list = list(Metabolite_synonym.objects.all().values_list('synonym',flat=True))
    db_list = tidy_synonym_list(db_list)
    
    print("Getting Model name list ...")
    name_list = Model_metabolite.objects.filter(source__name=model).values_list('name',flat=True)
    name_list = tidy_synonym_list(name_list)
    
    print("Getting Model ID list ...")
    id_list = Model_metabolite.objects.filter(source__name=model).values_list('model_id',flat=True)
    id_list = tidy_synonym_list(id_list)
    
    model_list = id_list + name_list
    
    model_db_list = Metabolite_synonym.objects\
        .filter(metabolite__model_metabolite__source__name=model)\
        .values_list('synonym', flat=True)
    model_db_list = tidy_synonym_list(model_db_list)
    
    model_aug_list = list(set(model_list + model_db_list))
    
    file_in_list = []
    raw_in_list = []
    for line in f_in:
        chemical_name = line.strip()
        file_in_list.append(chemical_name)
        raw_in_list.append(chemical_name)
        
        ## Look at brackets at the end of the line 
        
        end_brackets = re.search('^(.+)\(([^\(\)]+)\)$',chemical_name)
        
        if end_brackets:
            forename = end_brackets.group(1).strip()
            bracket_name = end_brackets.group(2).strip()
            file_in_list.append(forename)
            file_in_list.append(bracket_name)
            raw_in_list.append(chemical_name)
            raw_in_list.append(chemical_name)
        
        
    f_in.close()
    file_in_list_tidy = tidy_synonym_list(file_in_list)
    
    f_out.write("{}\t{}\t{}\t{}\n".format(
            "Name",
            "Synonym tested",
            "In model",
            "In DB"
        ))
    
    yes_priority = {}
    yes_priority['Yes'] = 1
    yes_priority['Yes L D'] = 2
    yes_priority['Yes L'] = 3
    yes_priority['Yes D'] = 4
    yes_priority['No'] = 5 
    
    results = []
    
    for idx, syn_in in enumerate(file_in_list_tidy):
        in_db = 'Yes'
        in_model = 'Yes'
        in_model_aug = 'Yes'
        
        if syn_in in db_list:
            pass
        else:
            if "d" + syn_in in db_list:
                in_db = in_db + " D" 
            if "l" + syn_in in db_list:
                in_db = in_db + " L"
            if in_db == 'Yes':
                in_db = 'No'
        if syn_in in model_list:
            pass
        else:
            if "d" + syn_in in model_list:
                in_model = in_model + " D" 
            if "l" + syn_in in model_list:
                in_model = in_model + " L"
            if in_model == 'Yes':
                in_model = 'No'
        if syn_in in model_aug_list:
            pass
        else:
            if "d" + syn_in in model_aug_list:
                in_model_aug = in_model_aug + " D" 
            if "l" + syn_in in model_aug_list:
                in_model_aug = in_model_aug + " L"
            if in_model_aug == 'Yes':
                in_model_aug = 'No'
        
#         f_out.write("{}\t{}\t{}\t{}\t{}\n".format(
#             raw_in_list[idx],
#             syn_in,
#             in_model,
#             in_model_aug,
#             in_db
#         ))
        results.append((
            raw_in_list[idx],
            syn_in,
            in_model,
            in_model_aug,
            in_db
        ))
        
    last_result = ("","","","","")
    match_results = []
    syn_list = [] 
    for current_result in results:
        
        name = current_result[0]
        synonym = current_result[1]
        
        mod = current_result[2]
        mod_db = current_result[3]
        db = current_result[4]
        
        if name == last_result[0]:
            syn_list.append(synonym)
            
            if yes_priority[mod] < yes_priority[last_result[2]]:
                match_results[0] = mod
            if yes_priority[mod_db] < yes_priority[last_result[3]]:
                match_results[1] = mod_db
            if yes_priority[db] < yes_priority[last_result[4]]:
                match_results[2] = db
        
        else:
            if len(last_result[0]) > 0:
                f_out.write("{}\t{}\t{}\t{}\n".format(
                    last_result[0],
                    ", ".join(syn_list),
#                     match_results[0],
                    match_results[1],
                    match_results[2],
                ))
            match_results = [mod, mod_db, db]
            syn_list = [synonym]
        
        last_result = current_result
    
    
    f_out.close()
            
def add_kegg_ids_as_synonyms(in_file=None):
    in_file = in_file or '/Users/wbryant/work/BTH/data/metanetx/chem_xref.csv'
    
    print("Getting synonym list ...")
    current_synonyms = set(Metabolite_synonym.objects.all().values_list('synonym', flat=True))
    print("Creating mnx_id - metabolite dictionary ...")
    mid_met_dict = get_model_dictionary(Metabolite, 'id')
    print("Beginning file analysis ...")
    
    
    source = Source.objects.get(name = 'kegg')
    source_name='kegg'
    
    f_in = open(in_file, 'r')
    
    num_source = 0
    for line in f_in:
        if re.match(source_name + "\:",line):
            num_source += 1
    f_in.close()
    f_in = open(in_file, 'r')
    
    print("Number of lines = {}".format(num_source))
    
#     counter = loop_counter(num_source, "{} lines finished".format(source_name))
    
    kegg_ids_checked = []
    
    line_no = 0
    for line in f_in:
        if not line.startswith("#"):
            if re.match(source_name + "\:",line):
                line_no += 1
#                 counter.step()
                kegg_id_entry = line.split("\t")[0].strip()
                mnx_id = line.split("\t")[1].strip()
                
                kegg_id = kegg_id_entry.split(":")[1].strip()
                
                if re.match('[A-Z][0-9]{5}',kegg_id):
#                     print kegg_id, mnx_id
                    if kegg_id not in kegg_ids_checked:
                        kegg_ids_checked.append(kegg_id)
                    else:
                        print("{} repeated in file ...".format(kegg_id))
                    if kegg_id in current_synonyms:
                        print(" - {} Already found ...".format(kegg_id))
                    else:
                        print("{}:\t{} being inputed ...".format(line_no, kegg_id))
                        
                        met = mid_met_dict[mnx_id]
                        
                        metsyn = Metabolite_synonym(
                            metabolite=met,
                            source=source,
                            synonym=kegg_id
                        )
                        
                        try:
                            metsyn.save()
                        except:
                            print(" - Save failed for ID {} ...".format(kegg_id))
                        
    f_in.close()
#     counter.stop()                
                    
                    
    
    
    