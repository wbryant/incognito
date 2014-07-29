"""
DEPRECATED?!
Model import via Annotation extended to COGzymes will be used for now.
"""

from django.core.management.base import BaseCommand, CommandError
from cogzymes.models import Gene, Organism, Cog, Cogzyme
from annotation.models import Reaction_synonym
from myutils.general.gene_parser import gene_parser
from myutils.SBML.import_SBML import import_SBML_to_bipartite as import_SBML
from myutils.SBML import calculate_stats as cas
import sys, re
from glob import glob
from time import time, gmtime, strftime

def import_model_sbml(import_file):
    """
    Import SBML file to NetworkX DiGraph, including GPR.
    """
    
    G = import_SBML(import_file)
    
    full_id = G.model_id
    model, species_id = full_id.split(" - ",1)        
    
    reactions = []
    for idx in G.nodes():
        if G.node[idx]["type"] == "reaction":
            
#             print("%s" % G.node[idx]["gpr"])
            
            
            node = G.node[idx]
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
            
            node["gpr"] = gpr
#             print("%s" % node["gpr"])
            
            id_rxn = re.sub("^R_","",node["id"])
            id_rxn = re.sub("_LPAREN_","(",id_rxn)
            id_rxn = re.sub("_RPAREN_",")",id_rxn)
            id_rxn = re.sub("_DASH_","-",id_rxn)
            node["id"] = id_rxn
            
            ##! Create node which is list of cas.enzymes
            
            enz_list = cas.create_enzyme_list(node)
            node["enzymes"] = enz_list
            
            #print("%s\n" % ", ".join(node["enzymes"]))
            
            
    return G, species_id, model    

def extract_cogzymes_from_enzymes(node, gene_cog_dict):
        """
        Add the COGs for a reaction in a DiGraph, according to the gene_cog_dict.
        
        """
        genes_not_found = []
        enzymes_not_found = []
        
        if node["type"] == "reaction":
            node["cogzymes"] = []
            for enzyme in node["enzymes"]:
                cog_list = []
                missing_cog = 0
                for gene in enzyme.gene_list:
                    if gene not in gene_cog_dict:
                        missing_cog = 1
                        if gene not in genes_not_found:
                            genes_not_found.append(gene)
                    else:
                        cogs = gene_cog_dict[gene]
                        for cog in cogs:
                            cog_list.append(cog)
                if missing_cog == 1:
                    enzymes_not_found.append(enzyme)
                else:
                    cogzyme = cas.Cogzyme(cog_list)
                    if cogzyme not in node["cogzymes"]:
                        node["cogzymes"].append(cogzyme)
            
        return genes_not_found, enzymes_not_found

class Command(BaseCommand):
    
    help = "Import an SBML model into the COGzymes database."
        
    def handle(self, *args, **options):
        """
        DEPRECATED?!  LOOK AT 
        Import an SBML model to the COGzymes database.
        The SBML should be that of an organism that is represented in eggNOG v3.0, with taxonomy ID in the organism table.
        
        Reaction data will be stored in the Annotation App, since this has already been developed.
        
        This will be under Model_reaction, and 
        """
        
        
        
        
        print "Start"
        
        if len(args) != 2:
            print("Exactly two arguments should be provided: the SBML file path and the source database for the model.")
            sys.exit(1)
        else:
            sbml_filename = args[0]
            source_db = args[1]
        
        
        
        ## Get network G (which includes Enzymes) and model_rxn_list
        
        G = import_SBML(sbml_filename)
        
        if G.species_id == 'Unknown':
            print("Species ID was not specified in SBML model ID.  Please use format 'model_id - taxonomy_id' for the model ID.")
            sys.exit(1)


        ## Create log file in same directory as SBML file to put in details of cogzyme import into database 
        
        log_file = re.sub("[^\.]+$",".log",sbml_filename)
        lf = open(log_file,"w")

        
        model_rxn_list = []
        for node in G.nodes():
            if G.node[node]["type"] == "reaction":
                model_rxn_list.append(G.node[node])
    
        lf.write("Log file for import of model {} (org ID: {}) to Cogzymes database at {}."\
                 .format(G.model_id, G.species_id, strftime("%Y-%m-%d %H:%M:%S - %d/%m/%Y", gmtime())))
        
        species_id = G.species_id
        
              
        ## Check whether organism exists and if not throw an error (will not find any COGs) 
        
        try:
            organism = Organism.objects.get(id=species_id)
        except:
            print("Organism with ID %s does not appear to be in COG/eggNOG, so cannot be imported." % species_id)
            sys.exit(1)
        
        
        ### Import all reactions
        
        rxn_nodes = []
        for idx in G.nodes():
            if G.node[idx]['type'] == 'reaction':
                rxn_nodes.append(G.node[idx])
        
        ### Reactions will be imported 
        
        
        
        
        