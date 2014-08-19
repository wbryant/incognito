'''
Created on Nov 8, 2013

@author: wbryant
'''

import networkx as nx
import re
from libsbml import SBMLReader
from myutils.SBML.gene_parser import gene_parser

# SBML import function
# This function imports an SBML model and converts it into a bipartite network
# of metabolites and reactions, noting weights for metabolites.

def import_SBML_to_bipartite(SBML_filename, parse_gprs = False, rxn_notes_fields = [], met_notes_fields = []):
    """Import file C{SBML_filename} and convert it into a bipartite metabolic network."""
    
    print '\n\nImporting SBML model ...'
    
    # Import SBML model
    reader = SBMLReader()
    document = reader.readSBMLFromFile(SBML_filename)
    model = document.getModel()
    print 'Model being imported: %s ...' % (model.getId())
    
    # Initialize NetworkX model and populate with metabolite and reaction nodes.
    # At the same time, create an id / node_idx dictionary for use when creating
    # edges.
    G = nx.DiGraph()
    node_idx = 0
    node_id_dictionary = {}
    
    try:
        model_id, species_id = model.getId().split(" - ",1)
        G.model_id = model_id
        G.species_id = species_id
    except:
        G.model_id = model.getId()
        G.species_id = 'Unknown'
    
    for metabolite in model.getListOfSpecies():
        node_idx += 1
        G.add_node(node_idx)
        G.node[node_idx]['name'] = metabolite.getName()
        G.node[node_idx]['id'] = metabolite.getId()
        G.node[node_idx]['type'] = 'metabolite'
        node_id_dictionary[metabolite.getId()] = node_idx
#         print metabolite.getId()
#         print node_id_dictionary[metabolite.getId()]
        

    for reaction in model.getListOfReactions():
        node_idx += 1
        G.add_node(node_idx)
        rxn_node = G.node[node_idx]
        rxn_node['name'] = reaction.getName()
        rxn_node['id'] = reaction.getId()
        rxn_node['type'] = 'reaction'
        node_id_dictionary[reaction.getId()] = node_idx
        
        #print node_idx
#         print rxn_node['name']
        
        notes = reaction.getNotesString()
        
        genelist = []
        genes = re.search('GENE[_ ]ASSOCIATION\:([^<]+)<',notes)
        if genes is not None:
            for gene in re.finditer('([^\s\&\|\(\)]+)', genes.group(1)):
                if not gene.group(1) == 'and' and not gene.group(1) == 'or' and not gene.group(1) == 'none':
                    genelist.append(gene.group(1))
            rxn_node['gpr'] = genes.group(1)
        else:
            rxn_node['gpr'] = 'None'
        rxn_node['genelist'] = list(set(genelist))
        
        ## If told to parse GPRs, create a list of enzyme 'names' (comma separated list of genes)
        if parse_gprs:
            gpr = rxn_node['gpr']
            rxn_node['enzymelist'] = []
            if gpr != 'None':
                for enzyme_name in gene_parser(gpr):
                    rxn_node['enzymelist'].append(enzyme_name)
        
        # Cycle through all reactants and products and add edges
        #print 'REACTANTS:'
        for reactant in reaction.getListOfReactants():
#             print reactant.getSpecies()
            reactant_idx = node_id_dictionary[reactant.getSpecies()]
            reactant_stoichiometry = -1*reactant.getStoichiometry()
            #print reactant_idx
            G.add_edge(reactant_idx,node_idx,coeff=reactant_stoichiometry)
            #print G.edges(reactant_idx)
        #print 'PRODUCTS:'
        for product in reaction.getListOfProducts():
            #print product.getSpecies()
            product_idx = node_id_dictionary[product.getSpecies()]
            product_stoichiometry = product.getStoichiometry()
            
            G.add_edge(node_idx,product_idx,coeff=product_stoichiometry)
            
            #print G.edges(node_idx)
        #print '\n'
    # Add degree of each metabolite as 'weight' attribute
    for node in G.nodes():
        if G.node[node]['type'] == 'metabolite':
            G.node[node]['weight'] = float(G.degree(node))
            G.node[node]['score'] = -1*float(G.degree(node))
    print 'Finished model import.'
    
    return G