from django.core.management.base import NoArgsCommand, CommandError
from annotation.models import Reaction, Evidence, Catalyst, Catalyst_ec, Enzyme, Gene
from gene_parser import gene_parser
import sys, re

# SBML import function
# This function imports an SBML model and converts it into a bipartite network
# of metabolites and reactions, noting weights for metabolites.
def import_SBML_to_bipartite(SBML_filename):
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
   
    for metabolite in model.getListOfSpecies():
        node_idx += 1
        G.add_node(node_idx)
        G.node[node_idx]['name'] = metabolite.getName()
        G.node[node_idx]['id'] = metabolite.getId()
        G.node[node_idx]['type'] = 'metabolite'
        node_id_dictionary[metabolite.getId()] = node_idx

    for reaction in model.getListOfReactions():
        node_idx += 1
        G.add_node(node_idx)
        G.node[node_idx]['name'] = reaction.getName()
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
        G.node[node_idx]['genelist'] = list(set(genelist))
	
        # Cycle through all reactants and products and add edges
	#print 'REACTANTS:'
        for reactant in reaction.getListOfReactants():
	    #print reactant.getSpecies()
	    reactant_idx = node_id_dictionary[reactant.getSpecies()]
	    #print reactant_idx
            G.add_edge(reactant_idx, node_idx)
	    #print G.edges(reactant_idx)
	#print 'PRODUCTS:'
        for product in reaction.getListOfProducts():
            #print product.getSpecies()
	    G.add_edge(node_idx,node_id_dictionary[product.getSpecies()])
	    #print G.edges(node_idx)
	#print '\n'
    # Add degree of each metabolite as 'weight' attribute
    for node in G.nodes():
        if G.node[node]['type'] == 'metabolite':
            G.node[node]['weight'] = float(G.degree(node))
	    G.node[node]['score'] = -1*float(G.degree(node))
    print 'Finished model import.'
    
    return G


class Command(NoArgsCommand):
    
    help = 'Imports data to the iAH991, Enzyme and Catalyst tables from the downloaded iAH991 reaction table.'
        
    def handle(self, **options):
        
        #Reaction.objects.all().delete()
        Evidence.objects.filter(source='iAH991').delete()
        Enzyme.objects.all().delete()
        Catalyst.objects.all().delete()
        
        #Enzymes (and link to genes)
        
        #Enzyme link to reactions
        
        f_in = open('/Users/wbryant/work/BTH/data/iAH991/iAH991_reactions.csv', 'r')
        #Populate: iAH991, Catalyst - DON'T DO EC, USE MOST SPECIFIC REACTION PREDICTIONS (I.E. TO Reaction)
        
        num_lines = 0
        for line in f_in:
            num_lines += 1
        f_in.close()
        f_in = open('/Users/wbryant/work/BTH/data/iAH991/iAH991_reactions.csv', 'r')
        
        print 'Populating iAH991, Enzyme and Catalyst table ...'
        #Initiate counter
        num_tot = num_lines
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()
        
        #create BiGG dictionary from Reaction to speed up table population
        bigg_rxn_dict = {}
        for rxn in Reaction.objects.all():
            list_of_bigg = rxn.bigg_id.strip().split(',')
            for bigg_id in list_of_bigg:
                bigg_rxn_dict[bigg_id] = rxn
        
        #Record number of reactions absent in MNXRef to be added to Reaction table
        num_mnx_absent = 0
        
        for line in f_in:
            line = line.split('\t')
            #print line
            
            bigg_id = line[1]
            function = line[2]
            gpr = line[4]
            confidence = line[5]
            #Ignore SEED IDs (use BiGG IDs), ignore EC numbers
            
            valid_gpr = False
            
            # Pull out enzymes
            if len(gpr) > 0:
                #print gpr
                enzymes_genes = gene_parser(gpr)
                valid_gpr = True
            
            if valid_gpr:
                source = 'iAH991'
                enzyme_list = []
                for enzyme_genes in enzymes_genes:
                    enzyme_name = enzyme_genes
                    genes = enzyme_name.split(',')
                    
                    if Enzyme.objects.filter(name=enzyme_name).count() > 0:
                        enzyme = Enzyme.objects.get(name=enzyme_name)
                    else:
                        enzyme = Enzyme(
                            name = enzyme_name,
                            source = source
                        )
                        enzyme.save()
                        for locus_tag in genes:
                            gene_found = False
                            try:
                                gene = Gene.objects.get(locus_tag=locus_tag)
                                gene_found = True
                            except:
                                print 'Locus tag %s could not be identified.' % locus_tag
                            if gene_found:
                                enzyme.genes.add(gene)
                    enzyme_list.append(enzyme)
                
            
                # Create foreign keys for Catalyst table
                try: 
                    reaction = bigg_rxn_dict[bigg_id]
                except:
                    #Reaction not found in MNXRef, so new reaction will be made
                    num_mnx_absent += 1
                    id = 'unknown%05d' % num_mnx_absent
                    #print '\nNon-MNXRef reaction found, new ID: %s\n' % id
                    reaction = Reaction(
                        id = id,
                        bigg_id = bigg_id
                    )
                    reaction.save()
                
                #Create score for evidence table
                score = float(confidence) / 4
                if score == 0:
                    score = 0.1
                
                
                evidence = Evidence(
                    source = 'iAH991',
                    score = score
                )
                evidence.save()
                
                #iah991 = iAH991(
                #    function = function,
                #    score = float(confidence)
                #)
                #iah991.save()
                
                #Create catalyst instance for each enzyme in the model
                for enzyme in enzyme_list:
                    catalyst = Catalyst(
                        enzyme = enzyme,
                        reaction = reaction,
                        evidence = evidence
                    )
                    catalyst.save()
        f_in.close()
