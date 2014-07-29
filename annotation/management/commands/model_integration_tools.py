from django.core.management.base import BaseCommand, CommandError
from annotation.models import Reaction, Stoichiometry, Metabolite, Compartment, Metabolite_synonym
import sys, os, re
from myutils.general.utils import loop_counter, dict_append
from libsbml import SBMLDocument, writeSBMLToFile, SBMLReader
import itertools
from copy import deepcopy

# Example species reference: '<speciesReference species="M_h_c" stoichiometry="1"/>'

def get_subsynonyms(synonym, re_terms = None):
    """Return subsynonyms of synonym with all permutations of expressions in re_terms removed by re.sub."""
    
    if re_terms == None:
        re_terms = [
            "[-_]",
            "[\(\)]",
            " ",
            "\([^\)]*\)$"
        ]
    
    subsynonyms = []
    
    for sub_list in itertools.permutations(re_terms):
        subsynonym = deepcopy(synonym)
        for sub_term in sub_list:
            subsynonym = re.sub(sub_term,"",subsynonym)
            if subsynonym != synonym:
                subsynonyms.append(subsynonym)
    
    subsynonyms = list(set(subsynonyms))
    
    return subsynonyms


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
            <parameter id="LOWER_BOUND" value="-1000" units="mmol_per_gDW_per_hr" constant="false"/>
            <parameter id="UPPER_BOUND" value="1000" units="mmol_per_gDW_per_hr" constant="false"/>
            <parameter id="FLUX_VALUE" value="0" units="mmol_per_gDW_per_hr" constant="false"/>
            <parameter id="OBJECTIVE_COEFFICIENT" value="0" units="mmol_per_gDW_per_hr" constant="false"/>
          </listOfParameters>
        </kineticLaw>
      </reaction>
"""

species_reference = u'          <speciesReference species="{}" stoichiometry="{}"/>\n'

species_declaration = u'      <species id="{}" name="{}" compartment="{}" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"></species>\n'



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
    mnxr_id = reaction_gpr_tuple[0]
    gpr = reaction_gpr_tuple[1]
    
    ## Get relevant reaction data - ID and name
    try:
        reaction = Reaction.objects.get(name=mnxr_id)
    except:
        print("Single reaction not found ...")
        sys.exit(1)
    
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
        
        species_declaration_list.append((full_met_id, metabolite.name, met_compartment))
        
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
    
    ## Create reaction string 
    reaction_xml = reaction_string.format(reaction_id, reaction_name, reaction_source,\
                                          gpr,substrate_string[:-1], product_string[:-1]) 
      
    return reaction_xml, species_declaration_list

def get_synonym_met_db():
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
    
    syn_met_dict = {}
    for synonym in synonym_dict:
        #print("Reaction '{}':".format(synonym))
        #print(" - synonym target: {}".format(synonym_dict[synonym][0]))
        try:
            
            metabolite = Metabolite.objects.get(id = synonym_dict[synonym][0])
#             print metabolite.id
            
        except:
            print synonym, synonym_dict[synonym]
            sys.exit(1)
        
        #print(" - name: {}".format(metabolite.name))
        
        syn_met_dict[synonym] = metabolite
        
        
    return syn_met_dict
    
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
    