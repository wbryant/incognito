from django.core.management.base import BaseCommand, CommandError
from annotation.models import Reaction, Stoichiometry, Metabolite, Compartment, Metabolite_synonym, Source, Model_reaction
from cogzymes.models import Reaction_pred, Cogzyme, Gene
import sys, os, re
from myutils.general.utils import loop_counter, dict_append, preview_dict
from myutils.django.cogzymes_utils import get_gpr_from_reaction
from libsbml import SBMLDocument, writeSBMLToFile, SBMLReader
from collections import Counter
from copy import deepcopy
from cogzymes.management.commands.classify_predictions_small import infer_rxn_enz_pairs_from_preds
from itertools import groupby, product
from math import sqrt
from cobra.io import read_sbml_model, write_sbml_model
import cobra

os.environ["PYTHONWARNINGS"] ="ignore"

# Example species reference: '<speciesReference species="M_h_c" stoichiometry="1"/>'

reaction_string = u"""      <reaction id="{reaction_id}" name="{reaction_name}" reversible="true">
        <notes>
          <body xmlns="http://www.w3.org/1999/xhtml">
            <p>SOURCE: {source_name}</p>
            <p>GENE_ASSOCIATION: {gene_association}</p>
          </body>
        </notes>
        <listOfReactants>
{reactants}
        </listOfReactants>
        <listOfProducts>
{products}
        </listOfProducts>
        <kineticLaw>
          <math xmlns="http://www.w3.org/1998/Math/MathML">
            <ci> FLUX_VALUE </ci>
          </math>
          <listOfParameters>
            <parameter id="LOWER_BOUND" value="{lower_bound}" units="mmol_per_gDW_per_hr" constant="false"/>
            <parameter id="UPPER_BOUND" value="{upper_bound}" units="mmol_per_gDW_per_hr" constant="false"/>
            <parameter id="FLUX_VALUE" value="0" units="mmol_per_gDW_per_hr" constant="false"/>
            <parameter id="OBJECTIVE_COEFFICIENT" value="0" units="mmol_per_gDW_per_hr" constant="false"/>
          </listOfParameters>
        </kineticLaw>
      </reaction>
"""

species_reference = u'          <speciesReference species="{}" stoichiometry="{}"/>\n'

species_declaration = u'      <species id="{species_id}" name="{species_name}" compartment="{compartment}" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"></species>\n'


class Command(BaseCommand):
    
    help = 'Take a set of reactions from the DB and export all to the SBML file given.'
        
    def handle(self, *args, **options):
        
        """ Export ICG predictions to SBML, along with a set of DB reactions if required. 
        """ 
        
        try:
            model_file_in = args[0]
            model_file_out = args[1]
            dev_model_id = args[2]
            dev_model = Source.objects.get(name=dev_model_id)
        except:        
            sys.exit(1)
            ## Set model and input/output files
            model_file_in = '/Users/wbryant/work/BTH/data/iAH991/BTH_with_gprs.xml'
            dev_model = Source.objects.get(name='iAH991')        
            try:
                model_file_out = args[0]
            except:
                model_file_out = '/Users/wbryant/work/BTH/analysis/working_models/scratch_model.xml'
        
        rem_prior = 0.9
        add_prior = 0.1
        
        ## Infer direct reaction/enzyme predictions from Reaction_preds for dev_model (InCOGnito)
        rxn_gpr_tuples = infer_rxn_enz_pairs_from_preds(dev_model)
         
        ## Run converter for selected reactions
        met_mapping_cutoff = 0.5
        rxns_added = convert_db_rxns_to_sbml(rxn_gpr_tuples, model_file_in, model_file_out, infer_gprs = False)
        
        ## Find removal predictions and note reaction IDs in relevant file, along with all added reaction IDs
        removal_reaction_list = list(Reaction_pred.objects.filter(
            dev_model=dev_model,
            status='rem')\
            .values_list('reaction__db_reaction__name', flat=True)\
            .distinct())
        
        ## Find relevant model reaction IDs and note in ABC file
        abc_file_out = '/Users/wbryant/work/MTU/gene_essentiality/abc-smc/data_files_corrected/pred_list.txt' 
        abc_file = open(abc_file_out, "w")
        for db_rxn in removal_reaction_list:    
            try:
                model_rxn_id = Model_reaction.objects.get(db_reaction=db_rxn, source=dev_model).model_id
            except:
                try:
                    model_rxn_id = Model_reaction.objects.get(db_reaction__name=db_rxn, source=dev_model).model_id
                except:
                    print("Could not find reaction for removal: '{}'".format(db_rxn))
                    continue
            abc_file.write("{}\t{}\n".format(model_rxn_id, rem_prior))            
        for rxn_id in rxns_added:
            abc_file.write("{}\t{}\n".format(rxn_id, add_prior))
        abc_file.close() 

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
    
    reaction_details = []
#     db_to_model_id_dict = {}
    new_metabolite = []

    all_rxn_xml = ''
    rxn_count_dict = {}
    added_rxns = []
    for rxn_gpr in rxn_gpr_tuples:
        
        reaction = rxn_gpr[0]
        gpr = rxn_gpr[1]
        
        reaction_id = reaction.name
        reaction_name = reaction.name
        reaction_source = reaction.source.name
        
        if reaction_id not in rxn_count_dict:
            rxn_count_dict[reaction_id] = 1
        else:
            rxn_count_dict[reaction_id] += 1
        
        id_suffix = "_enz" + str(rxn_count_dict[reaction_id])
        reaction_id += id_suffix
        
        ## Get reaction reversibility
        upper_bound = 1000
        lower_bound = -1000
        if reaction.reversibility_eqbtr > 0:
            lower_bound = 0
        elif reaction.reversibility_eqbtr < 0:
            upper_bound = 0
        
        stoichiometry = Stoichiometry.objects.filter(reaction=reaction)
        
        substrate_tuple_list = []
        product_tuple_list = []    
        
        balanced_reaction = True
        
        for met_sto in stoichiometry:
            ## For each metabolite in the stoichiometry, check whether it's in the model
            
            metabolite = met_sto.metabolite
#             met_name = metabolite.name.lower()
#             if (met_name[:2] == "a ") or (met_name[:3] == "an "):
#                 print met_name
             
            ## Get metabolite compartment 
            try:
                mnx_compartment = met_sto.compartment.values_list('id', flat=True)
            except:
                mnx_compartment = '' 
            if mnx_compartment == 'MNXC2':
                met_compartment = '_e'
            else:
                met_compartment = '_c'

            met_id = metabolite.id
            original_id = metabolite.id
            
            ## Potential matching DB synonyms to model metabolites
            synonym_list = db_met_syn_dict[met_id]
            
            ## Make compartment-specific synonyms
            synonym_list = [synonym + met_compartment for synonym in synonym_list]
            
            ## If there is a specific metabolite then find it.
            model_id = is_model_met(model_dict, synonym_list)
            
            if model_id is None:
                for synonym in synonym_list:
                    #print synonym
                    synonym = synonym[:-1] + comp_swap[synonym[-1:]]
                model_id_alt = is_model_met(model_dict, synonym_list)
                if model_id_alt is not None:
                    ## metabolite is found, but in the other compartment.
                    
                    model_id = model_id_alt[:-1] + comp_swap[synonym[-1:]]
                    print("Swapped compartment: {} - {}".format(met_id, model_id))
                else:
                    ## Metabolite is not found - try to find a seed ID
                    try:
                        met_id_list = Metabolite_synonym.objects\
                            .filter(metabolite=metabolite, source__name='seed')\
                            .values_list('synonym', flat=True)
                        met_id = min(met_id_list, key=len)
                    except:
                        pass
                    
                    model_id = "M_" + met_id + met_compartment
                
                ## Metabolite (incl. compartment) was not found - will be added to species declaration
                new_metabolite.append((model_id, original_id))
            else:
                model_id = "M_" + model_id
        
            ## Add to relevant part of equation
            if met_sto.stoichiometry < 0:
                substrate_tuple_list.append((model_id,abs(met_sto.stoichiometry)))
            elif met_sto.stoichiometry > 0:
                product_tuple_list.append((model_id,abs(met_sto.stoichiometry)))
            else:
                print("Metabolite '%s' (Reaction '%s') did not have valid stoichiometry ..." % (model_id, reaction_id))
                balanced_reaction = False
            
#             db_to_model_id_dict[met_id] = model_id
        
        if balanced_reaction:
            ## Create substrate and product strings
            substrate_string = ''
            for substrate in substrate_tuple_list:
                substrate_string += species_reference.format(*substrate)
            product_string = ''
            for product in product_tuple_list:
                product_string += species_reference.format(*product)
            
            ## Create reaction string 
            reaction_xml = reaction_string.format(
                reaction_id = reaction_id,
                reaction_name = reaction_name,
                source_name = reaction_source,
                gene_association = gpr,
                reactants = substrate_string[:-1],
                products = product_string[:-1],
                lower_bound = lower_bound,
                upper_bound = upper_bound) 
            
            if lower_bound == 0:
                print 'for', reaction_id
            elif upper_bound == 0:
                print 'back', reaction_id
            
            all_rxn_xml += reaction_xml
            added_rxns.append(reaction_id)
    
    ## Create XML for new species
    sp_string = ''
    for item in sorted(list(set(new_metabolite))):
        met_id = item[0]
        synonyms = Metabolite_synonym.objects.filter(metabolite__id = item[1]).values_list('synonym',flat=True)
        met_name = max(synonyms, key=len)
        met_comp = met_id[-1:]
        sp_string += species_declaration.format(
                            species_id = met_id,
                            species_name = met_name,
                            compartment = met_comp)
    
    ## Split input model and add reactions and species
    f_in = open(model_file_in,'r')
    f_out = open(model_file_out,'w')
     
    for line in f_in:
        if '</listOfSpecies>' in line:
            f_out.write(sp_string.encode('utf8'))
        elif '</listOfReactions>' in line:
            f_out.write(all_rxn_xml.encode('utf8'))
         
        f_out.write(line)
    
    f_in.close() 
    f_out.close()
    
    return added_rxns


def get_species_id_dict(model_file = '/Users/wbryant/work/BTH/data/iAH991/BTH_with_gprs.xml'):
    """ Return a dictionary of species IDs from IDs and names from the input model."""
    
    reader = SBMLReader()
    document = reader.readSBMLFromFile(model_file)
    model = document.getModel()
    
    species_id_dict = {}
    ambiguous_synonyms = []
    covered_metabolites = []
    for metabolite in model.getListOfSpecies():
        
        metabolite_id = metabolite.getId()
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

# def create_reaction_xml(reaction_gpr_tuple):
#     """ Return XML as close to SEED as possible, and species tuples."""
#     mnxr_id = reaction_gpr_tuple[0]
#     gpr = reaction_gpr_tuple[1]
#     
#     ## Get relevant reaction data - ID and name
#     try:
#         reaction = Reaction.objects.get(name=mnxr_id)
#     except:
#         print("Single reaction not found ...")
#         sys.exit(1)
#     
#     reaction_id = reaction.name
#     reaction_name = reaction.name
#     reaction_source = reaction.source.name
#     
#     stoichiometry = Stoichiometry.objects.filter(reaction=reaction)
#     
#     mets_found = 0
#     mets_tot = stoichiometry.count()
#     substrate_tuple_list = []
#     product_tuple_list = []
#     species_declaration_list = []
#     
#     for met_sto in stoichiometry:
#         
#         metabolite = met_sto.metabolite
#         
#         ## Get metabolite compartment 
#         try:
#             mnx_compartment = met_sto.compartment.values_list('id', flat=True)
#         except:
#             mnx_compartment = '' 
#         if mnx_compartment == 'MNXC2':
#             met_compartment = 'e'
#         else:
#             met_compartment = 'c'
#         
#         ## Is metabolite in SEED?
#         try:
#             met_id_list = Metabolite_synonym.objects\
#                 .filter(metabolite=metabolite, source__name='seed')\
#                 .values_list('synonym', flat=True)
#             met_id = min(met_id_list, key=len)
#             mets_found += 1
#         except:
#             met_id = metabolite.id
#         
#         full_met_id = 'M_' + met_id + '_' + met_compartment
#         
#         species_declaration_list.append((full_met_id, metabolite.name, met_compartment))
#         
#         if met_sto.stoichiometry < 0:
#             substrate_tuple_list.append((full_met_id,abs(met_sto.stoichiometry),metabolite.name))
#         elif met_sto.stoichiometry > 0:
#             product_tuple_list.append((full_met_id,abs(met_sto.stoichiometry),metabolite.name))
#         else:
#             print("Metabolite '%s' (Reaction '%s') did not have valid stoichiometry ..." % (full_met_id, reaction_id))
#             return '', ''
#     
#     ## Create substrate and product strings
#     substrate_string = ''
#     for substrate in substrate_tuple_list:
#         substrate_string += species_reference.format(*substrate)
#     product_string = ''
#     for product in product_tuple_list:
#         product_string += species_reference.format(*product)
#     
#     ## Create bounds
#     upper_bound = 1000
#     lower_bound = -1000
#     if reaction.reversibility_eqbtr > 0:
#         lower_bound = 0
#     elif reaction.reversibility_eqbtr < 0:
#         upper_bound = 0
#     
#     ## Create reaction string 
#     reaction_xml = reaction_string.format(
#         reaction_id,
#         reaction_name,
#         reaction_source,
#         gpr,
#         substrate_string[:-1],
#         product_string[:-1],
#         lower_bound,
#         upper_bound
#         ) 
#       
#     return reaction_xml, species_declaration_list

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

def create_species_xml(species_declaration_list, model_file = '/Users/wbryant/work/BTH/data/iAH991/BTH_with_gprs.xml'):
    """ Create XML for all species not already present in model_file."""
    
    model_dict = get_species_id_dict(model_file)
    db_met_synonym_dict = get_met_synonyms_db()
    
    ## Dictionary to store model IDs for DB mets found in the model
    model_metabolite_ids = {}
    
    ## Create species declarations
    species_declaration_string = ''
    for species_tuple in list(set(species_declaration_list)):
        
        query_species = species_tuple[0]
        
        model_species = is_model_met(model_dict, db_met_synonym_dict[query_species])
        
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
  
# NOT SURE THIS IS NECESSARY, JUST LOOK ON THE FLY    
# def find_novel_gprs_for_known_reactions(dev_model, pred_list):
#     """If any dev_model reactions have no GPR, see if the known predictions provide any."""
#     
#     ## find all dev_model reactions without GPRs
#     
#     ## Of those reactions, how many have predictions?
#     
#     ## Collate predictions for each one (treat each cogzyme for each reaction separately)
#     
#     ## Create 

def collate_predictions(dev_model, model_file_in, prior_novel_function = 0.1, prior_known_function = 0.9):
    """Get strings for all predictions ready for printing to file."""
    
    print("Inferring predictions ...")
    predictions = _infer_predictions(dev_model)
    print("Creating species_id_dict ...")
    model_dict = get_species_id_dict(model_file_in)
    print("Creating met_synonyms_dict ...")
    db_met_syn_dict = get_met_synonyms_db()
    
    num_unbalanced = 0
    num_known = 0
    new_metabolites = []
    candidate_reactions = {}
    reaction_xmls = {}
    reaction_types = {}
    counter = loop_counter(len(predictions), "Processing predictions:")
    for prediction in predictions:
        
        prediction.initialise_xml_output(model_dict, db_met_syn_dict)
        if prediction.model_reaction:
            if prediction.model_reaction.model_id=="rxn00376":
                print("This is the prediction for rxn00376:")
                print prediction.db_reaction.pk
                print prediction.cogzyme.pk
                print prediction.model_reaction
                
        if ((not prediction.model_reaction) and prediction.balanced_reaction):
            new_metabolites.extend(prediction.new_metabolites)
            prediction.create_reaction_xml()
            reaction_id = prediction.reaction_id
            reaction_types[reaction_id] = "novel"
            if reaction_id not in reaction_xmls:
                reaction_xmls[reaction_id] = prediction.reaction_xml
        elif prediction.model_reaction:
            reaction_id = prediction.model_reaction.model_id
            reaction_types[reaction_id] = "known"
            num_known += 1
        else:
            num_unbalanced += 1
        num_gprs = len(prediction.gprs)
        for gpr in prediction.gprs:
            ### Add confidence along with GPR
            prior_value = prediction.confidence / sqrt(num_gprs)
            if reaction_types[reaction_id] == "known":
                prior_value = prior_value * prior_known_function
            else:
                prior_value = prior_value * prior_novel_function
            dict_append(candidate_reactions, reaction_id, (gpr, prior_value))
        counter.step()
    counter.stop()
    
    num_novel_candidates = len(candidate_reactions) - num_known
    new_metabolites_nr = list(set(new_metabolites))
    print("Number of novel reactions = {}".format(num_novel_candidates))
    print("Number of known reactions = {}".format(num_known))
    print("Number of excluded (unbalanced) reactions = {}".format(num_unbalanced))
    print("Total new metabolite calls = {}".format(len(new_metabolites)))
    print("Number of nr new metabolites = {}".format(len(new_metabolites_nr)))
    return candidate_reactions, new_metabolites_nr, reaction_xmls, reaction_types
    
def write_predictions(
        dev_model,
        model_file_in,
        model_file_out,
        model_file_out_2,
        model_file_out_3,
        prior_file_out,
        candidate_reactions,
        new_metabolites_nr,
        reaction_xmls,
        reaction_types):
    """
    Take collated prediction output and print to XML file of model.
    """
    f_prior = open(prior_file_out, 'w')
    ### Create dictionaries of individual reaction XMLs and confidences
    
    full_reaction_xmls = []
    for rxn_id, gprs_confs in candidate_reactions.iteritems():
        if reaction_types[rxn_id] is not "known":
            outline_xml = reaction_xmls[rxn_id]
            for idx, gpr_conf in enumerate(gprs_confs):
                rxn_id_suffix = "_enz{}".format(idx+1)
                full_rxn_id = "{}{}".format(rxn_id, rxn_id_suffix)
                gpr = gpr_conf[0]
                confidence = gpr_conf[1]
                f_prior.write("{}\t{}\n".format(full_rxn_id, confidence))
                full_reaction_xml = outline_xml.format(full_rxn_id, gpr)
                full_reaction_xmls.append(full_reaction_xml)
        else:
            pass
    f_prior.close()
        
    ## Put all reaction XML together for output
    all_rxns_xml = ""
    for xml in full_reaction_xmls:
        all_rxns_xml += xml
    
    ## Create all metabolite XML and concatenate
    all_mets_xml = ""
    for met_data in new_metabolites_nr:
        all_mets_xml += species_declaration.format(*met_data)
    
    ### Export all XML, also add GPR to known reactions
    
    f_in = open(model_file_in,'r')
    f_out = open(model_file_out,'w')    
    for line in f_in:
        if '</listOfSpecies>' in line:
            f_out.write(all_mets_xml.encode('utf8'))
        elif '</listOfReactions>' in line:
            f_out.write(all_rxns_xml.encode('utf8'))
        f_out.write(line)
    f_in.close() 
    f_out.close()
    
    ## Look for novel enzymes for existing reactions
    novel_enzyme_reactions = []
    f_prior = open(prior_file_out, 'a')
    model = read_sbml_model(model_file_out)
    write_sbml_model(model, model_file_out_2)
    model = read_sbml_model(model_file_out_2)
    for rxn_id, gprs_confs in candidate_reactions.iteritems():
        if reaction_types[rxn_id] is "known":
            novel_enzyme_reactions.append(rxn_id)
            for idx, gpr_conf in enumerate(gprs_confs):
                rxn_id_suffix = "_novel_enz{}".format(idx+1)
                full_rxn_id = "{}{}".format(rxn_id, rxn_id_suffix)
                gpr = str(gpr_conf[0])                
                confidence = gpr_conf[1]
                ## Create new reaction, and modify ID and GPR
                new_reaction = deepcopy(model.reactions.get_by_id(rxn_id))
                new_reaction.id = full_rxn_id
                new_reaction.gene_reaction_rule = gpr
                model.add_reaction(new_reaction)
                ## Append a prior to prior file
                f_prior.write("{}\t{}\n".format(full_rxn_id, confidence))    
    write_sbml_model(model, model_file_out_3)
    f_prior.close()
    
    ## Find removal predictions and note reaction IDs in prior file
    removal_reaction_list = list(Reaction_pred.objects.filter(
        dev_model=dev_model,
        status='rem')\
        .values_list('reaction__db_reaction__name', flat=True)\
        .distinct())
    
    ## Find relevant model reaction IDs and note in ABC file
    print novel_enzyme_reactions
    f_prior = open(prior_file_out, 'a')
    for db_rxn in removal_reaction_list:    
        try:
            model_rxn_id = Model_reaction.objects.get(db_reaction=db_rxn, source=dev_model).model_id
        except:
            try:
                model_rxn_id = Model_reaction.objects.get(db_reaction__name=db_rxn, source=dev_model).model_id
            except:
                print("Could not find relevant reaction by either ID or name: '{}'".format(db_rxn))
                continue
        model_rxn_id = re.sub("^R_","",model_rxn_id)
        print model_rxn_id 
        if model_rxn_id not in novel_enzyme_reactions:
            f_prior.write("{}\trem\n".format(model_rxn_id))     
    f_prior.close()
    
    return model
    
def _infer_predictions(dev_model):
    """Collect predictions and do analyses."""
    
    ## Get all db_reaction/cogzyme pairs in predictions for dev_model
    predictions = []
    reaction_cogzyme_preds = Reaction_pred.objects\
        .filter(
            dev_model=dev_model,
            reaction__db_reaction__isnull=False)\
        .values("reaction__db_reaction__pk","cogzyme__pk")\
        .distinct()
    for rxn_cz in reaction_cogzyme_preds:
        new_pred_analysed = IncognitoPrediction(
                    dev_model, 
                    rxn_cz["reaction__db_reaction__pk"],
                    rxn_cz["cogzyme__pk"])
        predictions.append(new_pred_analysed)
    
    return predictions    

class IncognitoPrediction():
    """A specific reaction/cogzyme pair predicted by InCOGnito, along with the 
    analysis data for filtering."""
     
    def __init__(self, dev_model, db_reaction_id, cogzyme_id):
        self.db_reaction = Reaction.objects.get(pk=db_reaction_id)
        self.cogzyme = Cogzyme.objects.get(pk=cogzyme_id)
        self.dev_model = dev_model
        
        ## Number of ref_models predicting this reaction/cogzyme pair
        self.num_models_predicting = Reaction_pred.objects\
            .filter(
                dev_model=self.dev_model,
                reaction__db_reaction=self.db_reaction,
                cogzyme=self.cogzyme)\
            .values_list('ref_model__name', flat=True)\
            .distinct().count()
        
        self.num_ref_models = Reaction_pred.objects\
            .filter(dev_model=self.dev_model)\
            .values_list('ref_model__name', flat=True)\
            .distinct().count()
        
        self.proportion_models_predicting = float(self.num_models_predicting)/self.num_ref_models
        
        ## Proportion of reaction metabolites found in dev_model
        num_mets = self.db_reaction.stoichiometry_set.all().count()
        num_mets_mapped = self.db_reaction.stoichiometry_set\
            .filter(metabolite__model_metabolite__source=dev_model)\
            .distinct().count()
        self.mapped_proportion = float(num_mets_mapped)/num_mets       
        
        self.confidence = self.proportion_models_predicting * self.mapped_proportion
        if self.confidence == 0:
            ## If no mapped metabolites give arbitrary small confidence
            self.confidence = self.proportion_models_predicting * 0.1

        ## Infer all potential enzymes from gene locus constituents
        locus_cog_data = Gene.objects\
            .filter(
                organism__source=self.dev_model,
                cogs__cogzyme=self.cogzyme)\
            .values('locus_tag','cogs__name')
        cog_locus_dict = {}
        for locus_cog in locus_cog_data:
            dict_append(cog_locus_dict,locus_cog['cogs__name'],locus_cog['locus_tag'])
        cog_locus_lists = []
        for _, locus_list in cog_locus_dict.items():
            cog_locus_lists.append(locus_list)
        self.cog_locus_lists = cog_locus_lists
        self.enzyme_list = [list(genes) for genes in product(*cog_locus_lists)]
        
        self.num_reactions_for_this_cogzyme = Reaction.objects\
            .filter(model_reaction__cog_enzymes__cogzyme=self.cogzyme)\
            .distinct().count()
        
        ## Is reaction already in the model?
        try:
            self.model_reaction = Model_reaction.objects.get(source=self.dev_model, db_reaction=self.db_reaction)
        except:
            self.model_reaction = None
        
        self.new_metabolites = []
            
    def initialise_xml_output(self, model_dict, db_met_syn_dict, max_enzyme_candidates = 20):
        """Get the strings required for XML output."""
        
        ## Whether or not the reaction is in the model already, the new GPRs should be created in case the reaction does not hve one already
        if len(self.enzyme_list) <= max_enzyme_candidates:
            self.gprs = [" and ".join(gene_list) for gene_list in self.enzyme_list]
#             if len(self.cog_locus_lists) > 1:
#                 print(" - Locus lists:")    
#                 for locus_list in self.cog_locus_lists: 
#                     print locus_list
#                 print(" - enzyme list, GPRs:") 
#                 print self.enzyme_list
#                 print self.gprs
#                 print ""
        else:
            ## Create gpr strings for each COG in the cogzyme
            components = ["( " + " or ".join(gene_list) + " )" for gene_list in self.cog_locus_lists]
            ## Add the strings together into full GPR
            self.gprs = ["( " + " and ".join(components) + " )"]
#             print self.gprs[0]
        
        if not self.model_reaction:
            ## Reaction not in model, so create from db_reaction
            
            self.reaction_id = self.db_reaction.name
            self.reaction_name = self.db_reaction.name
            self.reaction_source = self.db_reaction.source            
            self.upper_bound = 1000
            self.lower_bound = -1000
            if self.db_reaction.reversibility_eqbtr > 0:
                self.lower_bound = 0
            elif self.db_reaction.reversibility_eqbtr < 0:
                self.upper_bound = 0            
            self._prepare_metabolite_xml(model_dict, db_met_syn_dict)
               
    def _prepare_metabolite_xml(self, model_dict, db_met_syn_dict):
        """Prepare XML from stoichiometry, including model metabolites where they can be found."""
        
        comp_swap = {}
        comp_swap['e'] = 'c'
        comp_swap['c'] = 'e'
        
        stoichiometry = Stoichiometry.objects.filter(reaction=self.db_reaction)
        substrate_tuple_list = []
        product_tuple_list = []
        new_metabolites = []    
        self.balanced_reaction = True
        
        if len(stoichiometry) == 2:
            if stoichiometry[0].metabolite == stoichiometry[1].metabolite:
                ## If the metabolites are the same, it is a transport reaction, so ensure that the two compartments are different.
                if stoichiometry[0].compartment == stoichiometry[1].compartment:
                    stoichiometry[0].compartment = Compartment.objects.get(id='MNXC2')
                    stoichiometry[1].compartment = Compartment.objects.get(id='MNXC3')
                    
        
        
        
        for entry in stoichiometry:
            ## For each metabolite in the stoichiometry, check whether it's in the model
            
            metabolite = entry.metabolite
            ## Get metabolite compartment 
            try:
                mnx_compartment = entry.compartment.id
            except:
                mnx_compartment = '' 
            if mnx_compartment == 'MNXC2':
                met_compartment = '_e'
            else:
                met_compartment = '_c'
                
            
            met_id = metabolite.id
            original_id = metabolite.id
            
            ## Potential matching DB synonyms to model metabolites
            synonym_list = db_met_syn_dict[met_id]
            
            ## Make compartment-specific synonyms
            synonym_list = [synonym + met_compartment for synonym in synonym_list]
            
            ## If there is a specific metabolite then find it.
            model_id = is_model_met(model_dict, synonym_list)
                    
            if model_id is None:
                for synonym in synonym_list:
                    #print synonym
                    synonym = synonym[:-1] + comp_swap[synonym[-1:]]
                model_id_alt = is_model_met(model_dict, synonym_list)
                if model_id_alt is not None:
                    ## metabolite is found, but in the other compartment.
                    
                    model_id = model_id_alt[:-1] + comp_swap[synonym[-1:]]
                    print("Swapped compartment: {} - {}".format(met_id, model_id))
                else:
                    ## Metabolite is not found - try to find a seed ID
                    try:
                        met_id_list = Metabolite_synonym.objects\
                            .filter(metabolite=metabolite, source__name='seed')\
                            .values_list('synonym', flat=True)
                        met_id = min(met_id_list, key=len)
                    except:
                        pass
                    
                    model_id = "M_" + met_id + met_compartment
                
                ## Conform to SBML specifications
                model_id = re.sub("[^a-zA-Z0-9_]+","__",model_id)
                ## Metabolite (incl. compartment) was not found - will be added to species declaration
                new_metabolites.append((model_id, original_id, met_compartment[-1]))
            else:
                model_id = "M_" + model_id

            ## Add to relevant part of equation
            if entry.stoichiometry < 0:
                substrate_tuple_list.append((model_id,abs(entry.stoichiometry)))
            elif entry.stoichiometry > 0:
                product_tuple_list.append((model_id,abs(entry.stoichiometry)))
            else:
#                 print("Metabolite '{}' (Reaction '{}') did not have valid stoichiometry ...".format(model_id, self.db_reaction.name))
                self.balanced_reaction = False    
#             db_to_model_id_dict[met_id] = model_id
        
        self.substrate_string = None
        self.product_string = None
        self.new_metabolites = []
        if self.balanced_reaction:
            ## Create substrate and product strings
            substrate_string = ''
            for substrate in substrate_tuple_list:
                substrate_string += species_reference.format(*substrate)
            product_string = ''
            for product in product_tuple_list:
                product_string += species_reference.format(*product)
            self.substrate_string = substrate_string.rstrip()
            self.product_string = product_string.rstrip()    
            self.new_metabolites = new_metabolites
        
        return None

    def create_reaction_xml(self):
        """After XML has been initialised, put it all together to create reaction XML.
        
        Do not include reaction ID, as it will need to be incremented for each cogzyme? 
        """
        self.reaction_xml = reaction_string.format(
            reaction_name = self.reaction_name,
            source_name = self.reaction_source,
            reactants = self.substrate_string,
            products = self.product_string,
            lower_bound = self.lower_bound,
            upper_bound = self.upper_bound)    
        
    def print_stats(self):
        print("Reaction '{}', COGzyme {}:".format(self.db_reaction, self.cogzyme))
        print(" - number of models predicting = {}".format(self.num_models_predicting))
        print(" - proportion of metabolites mapped = {}".format(self.mapped_proportion))
        print(" - number of reactions for this cogzyme = {}".format(self.num_reactions_for_this_cogzyme))
        print(" - number of candidate enzymes = {}".format(len(self.enzyme_list)))
    
    def print_enzymes(self):
        print("Candidate enzymes:")
        for idx, enzyme in enumerate(self.enzyme_list):
            print("{})\t{}".format(idx+1, enzyme))




#             ## Create reaction string 
#             reaction_xml = reaction_string.format(
#                 reaction_id,
#                 reaction_name,
#                 reaction_source,
#                 gpr,
#                 substrate_string[:-1],
#                 product_string[:-1],
#                 lower_bound,
#                 upper_bound)    
    
    
    
    
# class OutputPrediction():
#     """A container for the details of a specific XML reaction entry: db_reaction, 
#     model_reaction if found and GPR string."""
#     
#     def __init__(self, predictionAnalysed):
#         self.gpr_string = gpr_string
#         self.db_reaction = db_reaction
#         
#         try:
#             self.model_reaction = Model_reaction.objects.get(db_reaction=self.db_reaction)
#         except:
#             self.model_reaction = None
#     


       

                    
    