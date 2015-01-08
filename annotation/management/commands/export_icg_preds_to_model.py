from django.core.management.base import BaseCommand, CommandError
from annotation.models import Reaction, Stoichiometry, Metabolite, Compartment, Metabolite_synonym, Source, Model_reaction
from cogzymes.models import Reaction_pred
import sys, os, re
from myutils.general.utils import loop_counter, dict_append, preview_dict
from myutils.django.cogzymes_utils import get_gpr_from_reaction
from libsbml import SBMLDocument, writeSBMLToFile, SBMLReader
from collections import Counter
from copy import deepcopy
# from myutils.SBML.export_gpr_to_bth import gpr

# Example species reference: '<speciesReference species="M_h_c" stoichiometry="1"/>'

reaction_string = u"""      <reaction id="{}" name="{}" reversible="true">
        <notes>
          <body xmlns="http://www.w3.org/1999/xhtml">
            <p>SOURCE: {}</p>
            <p>GENE_ASSOCIATION: {}</p>
          </body>
        </notes>
        <listOfReactants>
{}
        </listOfReactants>
        <listOfProducts>
{}
        </listOfProducts>
        <kineticLaw>
          <math xmlns="http://www.w3.org/1998/Math/MathML">
            <ci> FLUX_VALUE </ci>
          </math>
          <listOfParameters>
            <parameter id="LOWER_BOUND" value="{}" units="mmol_per_gDW_per_hr" constant="false"/>
            <parameter id="UPPER_BOUND" value="{}" units="mmol_per_gDW_per_hr" constant="false"/>
            <parameter id="FLUX_VALUE" value="0" units="mmol_per_gDW_per_hr" constant="false"/>
            <parameter id="OBJECTIVE_COEFFICIENT" value="0" units="mmol_per_gDW_per_hr" constant="false"/>
          </listOfParameters>
        </kineticLaw>
      </reaction>
"""

species_reference = u'          <speciesReference species="{}" stoichiometry="{}"/>\n'

species_declaration = u'      <species id="{}" name="{}" compartment="{}" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"></species>\n'

def get_species_id_dict(model_file = '/Users/wbryant/work/BTH/data/iAH991/BTH_with_gprs.xml'):
    """ Return a dictionary of species IDs (excluding 'M_') from IDs and names from the input model."""
    
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
            met_id_orig = metabolite_id[2:]
        else:
            met_id = metabolite_id.lower().strip()
            met_id_orig = metabolite_id
        met_name = metabolite.getName().lower().strip()
        
        if met_id in species_id_dict:
            print("Ambiguous ID: {} - {} ({})".format(met_id, met_name, species_id_dict[met_id]))
            ambiguous_synonyms.append(met_id)
        else:
            species_id_dict[met_id] = met_id_orig
            
        if met_name in species_id_dict:
            if met_name != met_id:
                print("Ambiguous name: {} - {} ({})".format(met_name, met_id, species_id_dict[met_id]))
                ambiguous_synonyms.append(met_name)
        else:
            species_id_dict[met_name + metabolite_id[-2:]] = met_id_orig
        
    for ambiguous_synonym in ambiguous_synonyms:
        species_id_dict.pop(ambiguous_synonym, None)
        
        
    return species_id_dict

def create_reaction_xml(reaction_gpr_tuple):
    """ Return XML as close to SEED as possible, and species tuples."""
    reaction = reaction_gpr_tuple[0]
    gpr = reaction_gpr_tuple[1]
    
#     ## Get relevant reaction data - ID and name
#     try:
#         reaction = Reaction.objects.get(name=mnxr_id)
#     except:
#         print type(mnxr_id)
#         print("Single reaction not found for '{}' ('{}') ...".format(mnxr_id, gpr))
#         sys.exit(1)
    
    reaction_id = reaction.name
    reaction_name = reaction.name
    reaction_source = reaction.source.name
    
    stoichiometry = Stoichiometry.objects.filter(reaction=reaction)
    
    mets_found = 0
    mets_tot = stoichiometry.count()
    substrate_tuple_list = []
    product_tuple_list = []
    species_declaration_list = []
    
    for met_sto in stoichiometry:
        
        metabolite = met_sto.metabolite
        
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
            mets_found += 1
        except:
            met_id = metabolite.id
        
        full_met_id = 'M_' + met_id + '_' + met_compartment
        
        species_declaration_list.append((full_met_id, metabolite.name, met_compartment, metabolite))
        
        if met_sto.stoichiometry < 0:
            substrate_tuple_list.append((full_met_id,abs(met_sto.stoichiometry),metabolite.name))
        elif met_sto.stoichiometry > 0:
            product_tuple_list.append((full_met_id,abs(met_sto.stoichiometry),metabolite.name))
        else:
            print("Metabolite '%s' (Reaction '%s') did not have valid stoichiometry ..." % (full_met_id, reaction_id))
            return '', ''
    
    ## Create substrate and product strings
    substrate_string = ''
    for substrate in substrate_tuple_list:
        substrate_string += species_reference.format(*substrate)
    product_string = ''
    for product in product_tuple_list:
        product_string += species_reference.format(*product)
    
    ## Create bounds
    upper_bound = 1000
    lower_bound = -1000
    if reaction.reversibility_eqbtr > 0:
        lower_bound = 0
    elif reaction.reversibility_eqbtr < 0:
        upper_bound = 0
    
    ## Create reaction string 
    reaction_xml = reaction_string.format(
        reaction_id,
        reaction_name,
        reaction_source,
        gpr,
        substrate_string[:-1],
        product_string[:-1],
        lower_bound,
        upper_bound
        ) 
      
    return reaction_xml, species_declaration_list

def get_met_synonyms_db():
    """Get dictionary of unambiguous synonyms-to-metabolites, prioritising SEED IDs."""
    
    model_mets = []     
        
    num_single = 0
    num_multi = 0
    num_named = 0
    
    
    synonym_dict = {}
    source_dict = {}
    met_syns = Metabolite_synonym.objects.all().values_list('synonym','metabolite__id','source__name')
    
    
    ### Get synonyms from the database to try to identify all of the model metabolites 
#     print("Gathering raw synonyms ...")
#     counter = loop_counter(len(met_syns))
    amb_met_id = "#N/A"
    for syn in met_syns:
        
#         counter.step()
        
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
    
#     counter.stop()
    
    
#     print("Gathering alternative synonyms ...")
#     counter = loop_counter(len(met_syns))
    for syn in met_syns:   
         
#         counter.step()
         
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
    
#     counter.stop()
        
    ambiguous_synonyms = []
    for synonym in synonym_dict:
        synonym_dict[synonym] = list(set(synonym_dict[synonym]))
        if len(synonym_dict[synonym]) > 1:
            ambiguous_synonyms.append(synonym)
    
    for ambiguous_synonym in ambiguous_synonyms:
        synonym_dict.pop(ambiguous_synonym, None)
    
    
    ## Now reverse synonym dictionary so that mnx_id can be used to find all synonyms
#     print("Reversing dictionary ...")
#     counter = loop_counter(len(synonym_dict))
    met_syn_dict = {}
    for synonym in synonym_dict:
        met_id = synonym_dict[synonym][0]
        
        try:
            dict_append(met_syn_dict, met_id, synonym)
        except:
            print met_id, synonym
            sys.exit(1)
        
    return met_syn_dict
    
def is_model_met(model_dict, syn_list):
    """If synonyms in syn_list are uniquely mappable to single model met, return met ID."""
    
    ## Find all entries in model_dict corresponding to syn_list entries
    
    mappings = []
    for synonym in syn_list:
        if synonym in model_dict:
            mappings.append(model_dict[synonym])
    
    mappings = list(set(mappings))
    
    if len(mappings) == 1:
        return mappings[0]
    else:
        return None 

def create_species_xml(species_declaration_list, rxn_xml, model_file = '/Users/wbryant/work/BTH/data/iAH991/BTH_with_gprs.xml'):
    """ Create XML for all species not already present in model_file."""
    
    ## Link all IDs/names in the model to the relevant metabolite 
    model_dict = get_species_id_dict(model_file)
    
    ## Create set of synonyms for each dbmet (key is MNXM ID)
    db_met_synonym_dict = get_met_synonyms_db()
    
    ## Dictionary to store model IDs for DB mets found in the model
    model_metabolite_ids = {}
    
    ## Create species declarations
    species_declaration_string = ''
    for species_tuple in list(set(species_declaration_list)):
        
        dbmet = species_tuple[3]
        
        ## From list of synonyms for dbmet, can a single metabolite in the model be identified?
        model_species = is_model_met(model_dict, db_met_synonym_dict[dbmet.id])
        
        if model_species is None:
            species_declaration_string += species_declaration.format(*species_tuple)
        else:
            print("Model species found: '{}' (from '{}')".format(model_species, query_species))
            model_metabolite_ids[query_species] = model_species

    return species_declaration_string, model_metabolite_ids

def stop_db_rxns_in_sbml(
        db_rxn_list,
        dev_model, 
        model_file_in = '/Users/wbryant/work/BTH/analysis/working_models/scratch_model.xml',
        model_file_out = '/Users/wbryant/work/BTH/analysis/working_models/scratch_model_rem.xml'):
    """Take a list of DB reactions and set the associated model reaction bounds to 0. 
    """
    
    
    
    ## Find relevant model reaction IDs
    removal_model_rxn_ids = []
    for db_rxn in db_rxn_list:
        try:
            model_rxn_id = Model_reaction.objects.get(db_reaction=db_rxn, source=dev_model).model_id
        except:
            try:
                model_rxn_id = Model_reaction.objects.get(db_reaction__name=db_rxn, source=dev_model).model_id
            except:
                print db_rxn
                continue
        removal_model_rxn_ids.append(model_rxn_id)
    
    
    
    f_in = open(model_file_in,'r')
    f_out = open(model_file_out,'w')         
    
    ## Run through each line, finding the relevant IDs and when found change the upper and lower bound values to 0
    removed_reactions = []
    for line in f_in:
        f_out.write(line)
        search_results = re.search('reaction[_\s]*id=\"(?P<rxn_id>[^\"]+)\"',line)
        if search_results:
            model_rxn_id = search_results.group('rxn_id')
            if model_rxn_id in removal_model_rxn_ids:
                for line in f_in:
                    line_out = deepcopy(line)
                    if ('id="LOWER_BOUND"' in line) or ('id="UPPER_BOUND"' in line):
                        line_out = re.sub('value=\"[\-0-9]+\"','value="0"',line)
                        removed_reactions.append(model_rxn_id)
                    f_out.write(line_out)
                    if '</reaction>' in line:
                        break
    
    removed_reactions = set(removed_reactions)
    removal_model_rxn_ids = set(removal_model_rxn_ids)
    unremoved_reactions = list(removal_model_rxn_ids - removed_reactions)
    removed_reactions = list(removed_reactions)
    
#     print("Removed reactions:\n")
#     print removed_reactions
#     print("\nUnremoved reactions:\n")
#     print unremoved_reactions
    
    
    
    
def convert_db_rxns_to_sbml(rxn_gene_list, 
                            model_file_in = '/Users/wbryant/work/BTH/data/iAH991/BTH_with_gprs.xml', 
                            model_file_out = '/Users/wbryant/work/BTH/analysis/working_models/scratch_model.xml',
                            infer_gprs = True
                            ):
    """Take a list of reactions from the database and produce XML compatible with the model in model_file.
    
    Reaction list is IDs and gene dependencies from predictions in the DB.
    
    """
    
    comp_swap = {}
    comp_swap['e'] = 'c'
    comp_swap['c'] = 'e'
    
    ## Get dictionaries for metabolite IDs in both model and DB. 
    
    model_dict = get_species_id_dict(model_file_in)
    db_met_syn_dict = get_met_synonyms_db()
    
    if infer_gprs:
        ## Create tuples from rxn_gene_list with GPRs for each predicted reaction
        rxn_gpr_tuples = []
        prev_rxn_id = sorted(rxn_gene_list)[0][0]
        gene_list = [sorted(rxn_gene_list)[0][1]]
        for rxn_gene in sorted(rxn_gene_list)[1:]:
            rxn_id = rxn_gene[0]
            print type(rxn_id)
            gene_locus = rxn_gene[1]
            ## If 'gene_locus' is actually a GPR, wrap it in brackets if necessary
            if "and" in gene_locus:
                gene_locus = re.sub("(^.+$)","(\g<1>)",gene_locus)
            if rxn_id == prev_rxn_id:
                gene_list.append(gene_locus)
            else:
                gene_list = list(set(gene_list))
                rxn_gpr_tuples.append((prev_rxn_id," or ".join(gene_list)))
                prev_rxn_id = rxn_id
                gene_list = [gene_locus]
        gene_list = list(set(gene_list))
        rxn_gpr_tuples.append((rxn_id," or ".join(gene_list)))
    else:
        rxn_gpr_tuples = rxn_gene_list
    
    new_met_candidates = []
    all_rxn_xml = ''
    for rxn_gpr in rxn_gpr_tuples:
        ## Create reaction XML (with SEED IDs where possible)    
        reaction_xml, species_declaration_list = create_reaction_xml(rxn_gpr)
        all_rxn_xml += reaction_xml
        ## Add all species to list of candidates for declaration
        new_met_candidates.extend(species_declaration_list)
    
    ## Check all candidates for declaration and where metabolites can be 
    ## identified in the model just amend the ID in the reaction XML
    sp_string, _ = create_species_xml(new_met_candidates, all_rxn_xml, model_file_in)
    
    
        
        
#         reaction = rxn_gpr[0]
#         gpr = rxn_gpr[1]
#         
#         reaction_id = reaction.name
#         reaction_name = reaction.name
#         reaction_source = reaction.source.name
#         
#         if reaction_id not in rxn_count_dict:
#             rxn_count_dict[reaction_id] = 1
#         else:
#             rxn_count_dict[reaction_id] += 1
#         
#         id_suffix = "_enz" + str(rxn_count_dict[reaction_id])
#         reaction_id += id_suffix
#         
#         stoichiometry = Stoichiometry.objects.filter(reaction=reaction)
#         
#         substrate_tuple_list = []
#         product_tuple_list = []    
#         
#         balanced_reaction = True
#         
#         for met_sto in stoichiometry:
#             ## For each metabolite in the stoichiometry, check whether it's in the model
#             
#             metabolite = met_sto.metabolite
# #             met_name = metabolite.name.lower()
# #             if (met_name[:2] == "a ") or (met_name[:3] == "an "):
# #                 print met_name
#              
#             ## Get metabolite compartment 
#             try:
#                 mnx_compartment = met_sto.compartment.values_list('id', flat=True)
#             except:
#                 mnx_compartment = '' 
#             if mnx_compartment == 'MNXC2':
#                 met_compartment = '_e'
#             else:
#                 met_compartment = '_c'
# 
#             met_id = metabolite.id
#             original_id = metabolite.id
#             
#             ## Potential matching DB synonyms to model metabolites
#             synonym_list = db_met_syn_dict[met_id]
#             
#             ## Make compartment-specific synonyms
#             synonym_list = [synonym + met_compartment for synonym in synonym_list]
#             
#             ## If there is a specific metabolite then find it.
#             model_id = is_model_met(model_dict, synonym_list)
#             
#             if model_id is None:
#                 for synonym in synonym_list:
#                     #print synonym
#                     synonym = synonym[:-1] + comp_swap[synonym[-1:]]
#                 model_id_alt = is_model_met(model_dict, synonym_list)
#                 if model_id_alt is not None:
#                     ## metabolite is found, but in the other compartment.
#                     
#                     model_id = model_id_alt[:-1] + comp_swap[synonym[-1:]]
#                     print("Swapped compartment: {} - {}".format(met_id, model_id))
#                 else:
#                     ## Metabolite is not found - try to find a seed ID
#                     try:
#                         met_id_list = Metabolite_synonym.objects\
#                             .filter(metabolite=metabolite, source__name='seed')\
#                             .values_list('synonym', flat=True)
#                         met_id = min(met_id_list, key=len)
#                     except:
#                         pass
#                     
#                     model_id = "M_" + met_id + met_compartment
#                 
#                 ## Metabolite (incl. compartment) was not found - will be added to species declaration
#                 new_metabolite.append((model_id, original_id))
#             else:
#                 model_id = "M_" + model_id
#         
#             ## Add to relevant part of equation
#             if met_sto.stoichiometry < 0:
#                 substrate_tuple_list.append((model_id,abs(met_sto.stoichiometry)))
#             elif met_sto.stoichiometry > 0:
#                 product_tuple_list.append((model_id,abs(met_sto.stoichiometry)))
#             else:
#                 print("Metabolite '%s' (Reaction '%s') did not have valid stoichiometry ..." % (model_id, reaction_id))
#                 balanced_reaction = False
#             
#             db_to_model_id_dict[met_id] = model_id
#         
#         if balanced_reaction:
#             ## Create substrate and product strings
#             substrate_string = ''
#             for substrate in substrate_tuple_list:
#                 substrate_string += species_reference.format(*substrate)
#             product_string = ''
#             for product in product_tuple_list:
#                 product_string += species_reference.format(*product)
#             
#             ## Create reaction string
#             try:
#                 reaction_xml = reaction_string.format(reaction_id, reaction_name, reaction_source,
#                                                   gpr,substrate_string[:-1], product_string[:-1]) 
#             except:
#                 print("{}".format(reaction_id))
#                 print("{}".format(reaction_name))
#                 print("{}".format(reaction_source))
#                 print("{}".format(gpr))
#                 print("{}".format(substrate_string[:-1]))
#                 print("{}".format(product_string[:-1]))
#                 sys.exit(1)
#                 
#             all_rxn_xml += reaction_xml
#     
#     ## Create XML for new species
#     sp_string = ''
#     for item in sorted(list(set(new_metabolite))):
#         met_id = item[0]
#         synonyms = Metabolite_synonym.objects.filter(metabolite__id = item[1]).values_list('synonym',flat=True)
#         met_name = max(synonyms, key=len)
#         met_comp = met_id[-1:]
#         sp_string += species_declaration.format(met_id, met_name, met_comp)
    
    ## Split input model and add reactions and species
    f_in = open(model_file_in,'r')
    f_out = open(model_file_out,'w')
     
#     print all_rxn_xml
#     print sp_string
     
    for line in f_in:
        if '</listOfSpecies>' in line:
            f_out.write(sp_string.encode('utf8'))
        elif '</listOfReactions>' in line:
            f_out.write(all_rxn_xml.encode('utf8'))
         
        f_out.write(line)
    
    f_in.close() 
    f_out.close()

from cogzymes.management.commands.classify_predictions_small import infer_rxn_enz_pairs_from_preds


                    
class Command(BaseCommand):
    
    help = 'Take a set of reactions from the DB and export all to the SBML file given.'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        model_file_in = '/Users/wbryant/work/BTH/data/iAH991/BTH_with_gprs.xml'
        dev_model = Source.objects.get(name='iAH991')
        
        try:
            model_file_out = args[0]
        except:
            model_file_out = '/Users/wbryant/work/BTH/analysis/working_models/scratch_model.xml'
        
        rxn_gene_list = []
        
        
        ## Infer direct reaction/enzyme predictions from Reaction_preds for dev_model (InCOGnito)
        rxn_gpr_tuples = infer_rxn_enz_pairs_from_preds(dev_model)
         
        ## Run converter for selected reactions
        convert_db_rxns_to_sbml(rxn_gpr_tuples, model_file_in, model_file_out, infer_gprs = False)
        
        
        ## Find removal predictions and note reaction IDs in relevant file 
        
        rem_file_out = '/Users/wbryant/work/BTH/analysis/working_models/scratch_model_removals.txt' 
        
        removal_reaction_list = list(Reaction_pred.objects.filter(
            dev_model=dev_model,
            status='rem')\
            .values_list('reaction__db_reaction__name', flat=True)\
            .distinct())
        
        f_rem = open(rem_file_out, "w")
        
        ## Find relevant model reaction IDs
        removal_model_rxn_ids = []
        for db_rxn in removal_reaction_list:
            try:
                model_rxn_id = Model_reaction.objects.get(db_reaction=db_rxn, source=dev_model).model_id
            except:
                try:
                    model_rxn_id = Model_reaction.objects.get(db_reaction__name=db_rxn, source=dev_model).model_id
                except:
                    print db_rxn
                    continue
            f_rem.write("{}\n".format(model_rxn_id))            
#             removal_model_rxn_ids.append(model_rxn_id)
        f_rem.close()
#         
#         stop_db_rxns_in_sbml(removal_reaction_list, dev_model)
#         
        
        