'''
Created on Oct 14, 2013

@author: wbryant
'''

#import cobra
#from cobra.io.sbml import create_cobra_model_from_sbml_file as import_SBML
#from collections import Counter
import matplotlib.pyplot as plt
import sys, re, os
import argparse
from myutils.general.gene_parser import gene_parser
from myutils.SBML.import_SBML import import_SBML_to_bipartite as import_SBML
import networkx as nx

class Enzyme:
    """
    An enzyme, defined by the specific set of genes encoding that enzyme in a particular organism.
    """
    
    def __init__(self, gene_list = None):
        self.gene_list = gene_list or []
        self.gene_set = frozenset(gene_list)
        self.size = len(self.gene_set)
        self.reaction_list = []
    
    def __eq__(self, other):
        return self.gene_set == other.gene_set
    
    def __repr__(self):
        return "<Enzyme (genes: %s)>" % ",".join(self.gene_list)
    
    def __hash__(self):
        return(hash(self.gene_set))
        
    def add_genes(self, genes):
        if isinstance(genes, list):
            for gene in genes:
                self.gene_list.append(gene)
        else:
            self.gene_list.append(genes)
        self.gene_set = frozenset(self.gene_list)

class Cogzyme:
    """
    A cogzyme: the specific set of COGs (defined by relevant genes) that make up an enzyme in a particular organism.
    """
    
    def __init__(self, cog_list = None):
        self.cog_list = cog_list or []
        self.cog_set = frozenset(cog_list)
        self.size = len(self.cog_set)
        self.reaction_list = []
    
    def __eq__(self, other):
        return self.cog_set == other.cog_set
    
    def __repr__(self):
        return "<Cogzyme (COGs: %s)>" % ",".join(self.cog_list)
    
    def __hash__(self):
        return(hash(self.cog_set))
        
        
    def add_cogs(self, cog_input_list):
        for cog in cog_input_list:
            self.cog_list.append(cog)
            
        self.cog_list = list(set(self.cog_list))
        self.cog_set = frozenset(self.cog_list)
 
class MetabolicReaction:
    
    def __init__(self, reaction_id, gpr = None, gene_cog_dict = {}, mnxref_dict = None):
        self.id = reaction_id
        self.enzymes = []
        self.cogzymes = []
        self.gpr = gpr or ""
        if len(self.gpr) > 0:
            #print("GPR present ('%s'), calculating enzymes ..." % self.gpr)
            self.extract_enzymes_from_gpr()
            if len(gene_cog_dict) > 0:
                #print("Gene COG dict present, calculating cogzymes ...")
                self.extract_cogzymes_from_enzymes(gene_cog_dict)
        self.mnxref_id = None
        if mnxref_dict is not None:
            if reaction_id in mnxref_dict:
                self.mnxref_id = mnxref_dict[reaction_id]
            
    
    def __repr__(self):
        if self.mnxref_id is not None:
            return "<Reaction, ID: %s, MNXR ID: %s>" % (self.id, self.mnxref_id)
        else:
            return "<Reaction, ID: %s, no MNXRef ID>" % self.id
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return self.id == other.id
    
    def add_gpr(self, gpr):
        self.gpr = gpr
    
    def extract_enzymes_from_gpr(self):
        enzymes_genes = gene_parser(self.gpr)
        
        for enzyme_genes in enzymes_genes:
            enzyme = Enzyme(enzyme_genes.split(","))
            if enzyme not in self.enzymes:
                self.enzymes.append(enzyme)
        
        self.enzymes = list(set(self.enzymes))
    
    def extract_cogzymes_from_enzymes(self, gene_cog_dict):
        """
        Add the COGs for the reaction, according to the gene_cog_dict.
        
        """
        genes_not_found = []
        enzymes_not_found = []
        
        for enzyme in self.enzymes:
            cog_list = []
            missing_cog = 0
            for gene in enzyme.gene_list:
                if gene not in gene_cog_dict:
                    missing_cog = 1
                    if gene not in genes_not_found:
                        genes_not_found.append(gene)
                        #print("Gene %s has no associated COGs." % gene)
                else:
                    cogs = gene_cog_dict[gene]
                    for cog in cogs:
                        cog_list.append(cog)
            if missing_cog == 1:
                enzymes_not_found.append(enzyme)
                #print(" - Enzyme %s has no associated COGs." % enzyme)
                pass
            else:
                cogzyme = Cogzyme(cog_list)
                if cogzyme not in self.cogzymes:
                    self.cogzymes.append(cogzyme)
        
        self.cogzymes = list(set(self.cogzymes))
        
        return genes_not_found, enzymes_not_found
        #self.no_cog_genes = list(set(genes_not_found))
        #self.no_cogzyme_enzymes = list(set(enzymes_not_found))
        
        #if len(genes_not_found) > 0:
        #    print("The following genes do not have associated COGs:\n\n%s\n" % ", ".join(genes_not_found))
        
                
class MetabolicModel:
    """
    A class containing species ID, and a list of enzymes/cogzymes containing reaction lists.
    """
    
    def __init__(self, import_file = None, mnxref_dict = None, source_db_in = None):
        self.species_id = ''
        self.model = ''
        self.source = ''
        self.enzymes = {}
        self.cogzymes = {}
        self.no_cog_genes = []
        self.no_cogzyme_enzymes = []
        self.reactions = []
        self.G = []
        self.gene_cog_dict = {}
        source_db = source_db_in or ''
        
        if import_file:
            self.import_model_sbml(import_file, mnxref_dict, source_db)
            self.initialize_gene_cog_dict()
            self.extract_reactions_cogzymes()
            self.update_enzyme_dict()
            self.update_cogzyme_dict()
            #if mnxref_dict:
            #    self.update_reaction_mnxref_ids(mnxref_dict)
    
    def __repr__(self):
        return "Metabolic Model %s (source: %s)" % (self.model, self.source)
    
    def __hash__(self):
        return hash(tuple(self.model, self.species_id, self.source))
    
    def __eq__(self, other):
        return tuple(self.model, self.species_id, self.source) == tuple(other.model, other.species_id, other.source)
    
    def update_reaction_mnxref_ids(self, mnxref_dict):
        pass
    
    def extract_reactions_cogzymes(self):
        
        no_cog_genes = []
        no_cogzyme_enzymes = []
        
        for reaction in self.reactions:
            reaction.extract_enzymes_from_gpr()
            genes_not_found, enzymes_not_found = reaction.extract_cogzymes_from_enzymes(self.gene_cog_dict)
            no_cog_genes.extend(genes_not_found)
            no_cogzyme_enzymes.extend(enzymes_not_found)
        
        self.no_cog_genes = list(set(no_cog_genes))
        self.no_cogzyme_enzymes = list(set(no_cogzyme_enzymes))
        
        print("Genes not found:\n\n - %s" % "\n - ".join(self.no_cog_genes))
        no_cogzyme_enzymes_names = []
        for nce in self.no_cogzyme_enzymes:
            no_cogzyme_enzymes_names.append(str(nce))
        print("\nEnzymes not found:\n\n - %s" % "\n - ".join(no_cogzyme_enzymes_names))
    
    def update_enzyme_dict(self):
        self.enzymes = {}
        for rxn in self.reactions:
            for enzyme in rxn.enzymes:
                if enzyme in self.enzymes:
                    self.enzymes[enzyme].append(rxn)
                else:
                    self.enzymes[enzyme] = [rxn]
    
    def update_cogzyme_dict(self):
        self.cogzymes = {}
        for rxn in self.reactions:
            for cogzyme in rxn.cogzymes:
                if cogzyme in self.cogzymes:
                    self.cogzymes[cogzyme].append(rxn)
                else:
                    self.cogzymes[cogzyme] = [rxn]
            
    def add_reactions(self, rxns):
        for rxn in rxns:
            if rxn not in self.reactions:
                self.reactions.append(rxn)
        self.update_enzyme_dict()
        self.update_cogzyme_dict()

    def initialize_gene_cog_dict(self, cog_files_in = None):
        """
        Retrieve from cog_file the COGs for all genes from the relevant species, as specified by species_id.
        """
        
        cog_files = cog_files_in or ["/Users/wbryant/work/cogzymes/eggNOG_data/COG.members.txt","/Users/wbryant/work/cogzymes/eggNOG_data/NOG.members.txt"]
        gene_cog_dict = {}
        
        for cog_file in cog_files:
            f_in = open(cog_file, "r")
            
            for line in f_in:
                cols = line.split("\t")
                #print cols[1]
                species, gene = cols[1].split(".",1)
                
                if species == self.species_id:
                    cog = cols[0]
                    if gene in gene_cog_dict:
                        gene_cog_dict[gene].append(cog)
                    else:
                        gene_cog_dict[gene] = [cog]
            f_in.close()
            
        self.gene_cog_dict =  gene_cog_dict
        
#     def initialise_gene_cog_dict(self, cog_file):
#         """
#         Retrieve from cog_file the COGs for all genes from the relevant species, as specified by species_id.
#         """
#         
#         f_in = open(cog_file, "r")
#         gene_cog_dict = {}
#         
#         for line in f_in:
#             cols = line.split("\t")
#             #print cols
#             species, gene = cols[1].split(".",1)
#             
#             if species == self.species_id:
#                 cog = cols[0]
#                 if gene in gene_cog_dict:
#                     gene_cog_dict[gene].append(cog)
#                 else:
#                     gene_cog_dict[gene] = [cog]
#         
#         f_in.close()
#         
#         self.gene_cog_dict = gene_cog_dict
    
    def import_model_sbml(self, import_file, mnxref_dict, source_db = None):
        """
        Import SBML file to this model, calculating all available cogzymes.
        """
        
        #self.species_id = species_id
        self.source_db = source_db or 'unknown'
        self.G = import_SBML(import_file)
        
        full_id = self.G.model_id
        
        
        self.model, self.species_id = full_id.split(" - ",1)        
        
        reactions = []
        for idx in self.G.nodes():
            if self.G.node[idx]["type"] == "reaction":
                
                node = self.G.node[idx]
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
                
                id_rxn = re.sub("^R_","",node["id"])
                id_rxn = re.sub("_LPAREN_","(",id_rxn)
                id_rxn = re.sub("_RPAREN_",")",id_rxn)
                id_rxn = re.sub("_DASH_","-",id_rxn)
                
                #print mnxref_dict
                
                reaction = MetabolicReaction(id_rxn, gpr, self.gene_cog_dict, mnxref_dict)
                reactions.append(reaction)
                
        self.add_reactions(reactions)
        
    
def create_enzyme_list(node):
    """
    Method for metabolic reaction nodes (in NetworkX format) to create a list of Enzymes (from Enzyme class) for that node.
    """
    
#    print("Getting enzyme list ...")
    
    enzyme_list = []
    
    if node["type"] != "reaction":
        return []
    else:
        if (len(node["genelist"]) == 0) & (len(node["gpr"]) == 0):
            return []
        else:
            gpr = node["gpr"]
            enz_genes_list = gene_parser(gpr)
            
            for enz_genes in enz_genes_list:
                gene_list = enz_genes.split(",")
                enzyme = Enzyme(gene_list)
                enzyme_list.append(enzyme)
    
#    print("Finished getting enzyme list ...")
    
    return enzyme_list

def enzyme_distribution(G):
    """
    Method for finding each enzyme in a network G and finding how many reactions each enzyme catalyzes. 
    """
    
    enzyme_dict = {}
    
    for idx in G.nodes():
        if G.node[idx]["type"] == "reaction":
            enzyme_list = create_enzyme_list(G.node[idx])
            for enzyme in enzyme_list:
                if enzyme in enzyme_dict:
                    enzyme_dict[enzyme] += 1
                else:
                    enzyme_dict[enzyme] = 1
    
    ## Look at stats
    
    enz_rxn_count_list = []
    enzyme_size_x = []
    enzyme_num_rxns_y = []
    
    for enzyme in enzyme_dict:
        enz_rxn_count_list.append(enzyme_dict[enzyme])
        
        enzyme_size_x.append(enzyme.size)
        enzyme_num_rxns_y.append(enzyme_dict[enzyme])
    
#     plt.scatter(enzyme_size_x,enzyme_num_rxns_y)
#     plt.xlim((0,14))
#     plt.ylim((0,25))
#     plt.show()
    
    ## Plot enzyme reaction counts bar chart
    
    return enz_rxn_count_list

def get_gene_cog_dict(species_id, cog_files_in = None):
    """
    Retrieve from cog_file the COGs for all genes from the relevant species, as specified by species_id.
    """
    
    cog_files = cog_files_in or ["/Users/wbryant/work/cogzymes/eggNOG_data/COG.members.txt","/Users/wbryant/work/cogzymes/eggNOG_data/NOG.members.txt"]
    gene_cog_dict = {}
    
    for cog_file in cog_files:
        f_in = open(cog_file, "r")
        
        for line in f_in:
            cols = line.split("\t")
            species, gene = cols[1].split(".")
            
            if species == species_id:
                cog = cols[0]
                if gene in gene_cog_dict:
                    gene_cog_dict[gene].append(cog)
                else:
                    gene_cog_dict[gene] = [cog]
        f_in.close()
        
    return gene_cog_dict

def import_gprs_iAH991(filename = "/Users/wbryant/work/BTH/data/iAH991/iAH991_reactions.csv"):
    """
    Get bth GPRs from the csv file in which they are located, and return a dctionary using reaction ID as the key.
    """
    
    id_gpr_dict = {}
    
    f_in = open(filename, "r")
    for line in f_in:
        line = line.split('\t')
        #print line
        
        idn = line[1]
        #idn = re.sub("^R_","",idn)
        gpr = line[4]
        
        #print("ID '%s': '%s' ..." % (idn, gpr))
        
        id_gpr_dict[idn] = gpr
    
    f_in.close()
    
    return id_gpr_dict

def initialise_iAH991_model(mnxref_dict):
    """
    Due to the GPR of iAH991 not being in the metabolic model, it is required that there is a special function for importing it into the class created here.
    """
    
    M = MetabolicModel()
    M.import_model_sbml("/Users/wbryant/work/cogzymes/models/bth_iah991.xml",mnxref_dict) 
    id_gpr_dict = import_gprs_iAH991()
    M.initialize_gene_cog_dict()
        
    for reaction in M.reactions:
        if reaction.id in id_gpr_dict:
            reaction.gpr = id_gpr_dict[reaction.id]
            #print("Importing '%s' GPR: '%s'" % (reaction.id, reaction.gpr))
            reaction.extract_enzymes_from_gpr()
            reaction.extract_cogzymes_from_enzymes(M.gene_cog_dict)
        else:
            print("Reaction (ID: '%s') not present in CSV file." % reaction.id)
    
    M.update_enzyme_dict()
    M.update_cogzyme_dict()
    
    return M

def compare_MM_cogzymes(M1,M2):
    """
    Look for cogzymes present in both MetabolicModels and show their respective reactions.
    """
    
    for m1_cogzyme in M1.cogzymes:
        if m1_cogzyme in M2.cogzymes:
            if (m1_cogzyme.size > 1):
                m1_reactions = M1.cogzymes[m1_cogzyme]
                m2_reactions = M2.cogzymes[m1_cogzyme]
                
                print("%s:" % str(m1_cogzyme))
                print(" - %s reactions:\n   - %s" % (M1.model, class_join(m1_reactions,"\n   - ")))
                print(" - %s reactions:\n   - %s\n" % (M2.model, class_join(m2_reactions,"\n   - ")))

def infer_missing_function_from_cogzymes(M1, M2):
    """
    Take two annotated models (with GPRs) and find cogzymes that confer different reactions in the different models.
    """
    
    examples_found = 0
    
    for m1_cogzyme in M1.cogzymes:
        
        if examples_found > 9:
            break
        
        if m1_cogzyme in M2.cogzymes:

            m1_reactions = M1.cogzymes[m1_cogzyme]
            m2_reactions = M2.cogzymes[m1_cogzyme]
            
            r1_only, r2_only, r1_and_r2 = compare_reaction_list(m1_reactions, m2_reactions)
            
            if (len(r1_only) > 0):
                examples_found += 1
                
                print("%s catalyzes the following reactions in %s but not in %s:\n   - %s\n" % (m1_cogzyme, M1.model, M2.model, class_join(r1_only,"\n   - ")))
                
                
  
    
    
    pass

def compare_reaction_list(rlist1,rlist2):
    """
    Compare two lists of reactions - output those common to both, and those unique to each.
    """
    r1_only = []
    r2_only = []
    r1_and_r2 = []
    
    for reaction in rlist1:
        if reaction in rlist2:
            r1_and_r2.append(reaction)
        else:
            r1_only.append(reaction)
    
    for reaction in rlist2:
        if reaction not in rlist1:
            r2_only.append(reaction)
    
    return r1_only, r2_only, r1_and_r2
     
                
def class_join(join_list, join_string):
    """
    For a list of classes, join the strings of those classes using the join string.
    """
    strings = []
    for join_class in join_list:
        strings.append(str(join_class))
    
    return join_string.join(strings)
    
def import_mnxref_dict(mnxref_file = "/Users/wbryant/work/cogzymes/data/reac_xref130614.tsv"):
    """
    Import all mapped names from MNXRef tsv file into a dictionary to try to convert any reaction names to the common MNXRef namespace.
    """
    
    f_in = open(mnxref_file, "r")
    
    ## Skip comments
    line = f_in.readline()
    while line[0] == "#":
        line = f_in.readline()
    
    mnxref_dict = {}
    mnxref_dup_dict = {}
    
    for line in f_in:
        r_id_tot, mnxref_id = line.strip().split("\t")
        r_id = r_id_tot.split(":")[1]
        
        if r_id in mnxref_dict:
            if mnxref_id != mnxref_dict[r_id]:
                mnxref_dict[r_id]  = 'duplicate'
                print("Duplicate ID found with '%s' := '%s', original is '%s' := '%s'." % (r_id_tot, mnxref_id, mnxref_dup_dict[r_id], mnxref_dict[r_id]))
        else:
            mnxref_dict[r_id] = mnxref_id
            mnxref_dup_dict[r_id] = r_id_tot
    
    r_dups = []
    for r_id in mnxref_dict:
        if mnxref_dict[r_id] == 'duplicate':
            r_dups.append(r_id)
    for r_dup in r_dups:
        del mnxref_dict[r_dup] 
    
    return mnxref_dict

"""
What questions should I be asking?

"""
    
if __name__ == '__main__':
    """!
    Take input SBML file and calculate:
    
    i)     the frequency distribution of multifunctionality of genes,
    ii)    the frequency distribution of number of enzymes (and num of genes) per reaction,
    iii)   
    
    !"""
    
    ## 
    
    
    """
    IPTYHON code
    
    model = import_SBML('eco_iAF1260.xml')
    gene_multifunc = []
    for gene in model.genes:
        gene_multifunc.append(len(gene.get_reaction()))
    print(Counter(gene_multifunc))
    import re
    for rxn in model.reactions:
        print rxn.gene_reaction_rule
        count = re.search("(and)",rxn.gene_reaction_rule)
        print len(count)
    """
    
    pass