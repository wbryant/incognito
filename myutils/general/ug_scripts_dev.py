from libsbml import SBMLReader
import networkx as nx
import re

# SBML import function
# This function imports an SBML model and converts it into a bipartite network
# of metabolites and reactions, noting weights for metabolites.
def import_SBML(SBML_filename, rxn_notes_fields = [], met_notes_fields = []):
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
    G.model_id = model.getId()
    node_idx = 0
    node_id_dictionary = {}
   
    for metabolite in model.getListOfSpecies():
        node_idx += 1
        G.add_node(node_idx)
        G.node[node_idx]['name'] = metabolite.getName().strip()
        G.node[node_idx]['id'] = metabolite.getId()
        G.node[node_idx]['type'] = 'metabolite'
        node_id_dictionary[metabolite.getId()] = node_idx

    for reaction in model.getListOfReactions():
        node_idx += 1
        G.add_node(node_idx)
        G.node[node_idx]['name'] = reaction.getName().strip()
        G.node[node_idx]['id'] = reaction.getId()
        G.node[node_idx]['type'] = 'reaction'
        node_id_dictionary[reaction.getId()] = node_idx
        
        #print node_idx
        #print G.node[node_idx]['name']
        
        notes = reaction.getNotesString()
        
        genelist = []
        genes = re.search('GENE[_ ]ASSOCIATION\:([^<]+)<',notes)
        if genes is not None:
            for gene in re.finditer('([^\s\&\|\(\)]+)', genes.group(1)):
                if not gene.group(1) == 'and' and not gene.group(1) == 'or' and not gene.group(1) == 'none':
                    genelist.append(gene.group(1))
            G.node[node_idx]['gpr'] = genes.group(1)
        else:
            G.node[node_idx]['gpr'] = 'None'
        G.node[node_idx]['genelist'] = list(set(genelist))
        
        # Cycle through all reactants and products and add edges
        #print 'REACTANTS:'
        for reactant in reaction.getListOfReactants():
            #print reactant.getSpecies()
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

def import_model_sbml(import_file, gpr_file):
    """
    Import SBML file to NetworkX DiGraph, including GPR.
    """

    ### Get GPRs from spreadsheet file for iAH991
    
    f_in = open(gpr_file, "r")
    
    rxn_gpr_dict = {}
    rxn_seed_dict = {}
    
    print("Importing GPRs from file...")
    
    for line in f_in:
        line = line.split('\t')    
        seed_id = line [0] #Capture in case BiGG ID is not found
        bigg_id = line[1]
        gpr = line[4]
            
        rxn_gpr_dict[bigg_id] = gpr
        rxn_seed_dict[bigg_id] = seed_id

    
    G = import_SBML(import_file)
    
    full_id = G.model_id
    print full_id
    model, species_id = full_id.split(" - ",1)        
    
    print("Adding GPRs to network ...")
    
    reactions = []
    for idx in G.nodes():
        if G.node[idx]["type"] == "reaction":
            node = G.node[idx]
            
            #print("Standardising reaction ID ...")
            
            id_rxn = re.sub("^R_","",node["id"])
            id_rxn = re.sub("_LPAREN_","(",id_rxn)
            id_rxn = re.sub("_RPAREN_",")",id_rxn)
            id_rxn = re.sub("_DASH_","-",id_rxn)
            node["id"] = id_rxn
            
            #print("Adding GPR ...")
            
            if node["id"] not in rxn_gpr_dict:
                print("GPR for '%s' not found ..." % node["id"])
                gpr = ""
            else:
                node["gpr"] = rxn_gpr_dict[node["id"]]
                
                if node["gpr"] == "None":
                    gpr = ""
                else:
                    gpr = node["gpr"]
                    
                gpr = gpr.strip()
                gpr = re.sub("AND","and",gpr)
                gpr = re.sub("OR","or",gpr)
                
                exceptions_list = ["Hypothetical","hypothetical","spontaneous","Spontaneous"]
                
                if gpr in exceptions_list:
                    gpr = ""
                
                ## Fill in gene list for current reaction
                
                genelist = re.findall('BT\_[0-9]{4}',gpr)
                node['genelist'] = genelist
                
            node["gpr"] = gpr
            #print("GPR: %s" % node["gpr"])
            
    return G, species_id, model, rxn_seed_dict
