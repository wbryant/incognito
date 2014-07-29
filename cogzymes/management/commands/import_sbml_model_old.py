from django.core.management.base import BaseCommand, NoArgsCommand, CommandError
from cogzymes.models import *
#from myutils.general.gene_parser import gene_parser
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

def dict_append(dict,key,value):
    """
    If a key is present in the dictionary append value to its value, else create a new entry with value as first member of list.
    """
    if key in dict:
        dict[key].append(value)
    else:
        dict[key] = [value]


class Command(BaseCommand):
    
    help = "Import an SBML model into the COGzymes database."
        
    def handle(self, *args, **options):
        
        print "Start"
        
        
        
        if len(args) != 2:
            print("Exactly two arguments should be provided: the SBML file path and the source database for the model.")
            sys.exit(1)
        else:
            sbml_filename = args[0]
            source_db = args[1]
        
        ##! Create log file in same directory as SBML file to put in details of cogzyme import into database 
        
        log_file = re.sub("[^\.]+$",".log",sbml_filename)
        
        lf = open(log_file,"w")
        
        
        ## Get network G (which includes Enzymes) and model_rxn_list
        
        G, species_id, model_id = import_model_sbml(sbml_filename)
        
        model_rxn_list = []
        for node in G.nodes():
            if G.node[node]["type"] == "reaction":
                model_rxn_list.append(G.node[node])
    
        lf.write("Log file for import of model %s (org ID: %s) to Cogzymes database at %s." % 
            (model_id, species_id, strftime("%Y-%m-%d %H:%M:%S - %d/%m/%Y", gmtime())))
        
              
        ## Check whether organism exists and if not throw an error (will not find any COGs) 
        
        if Organism.objects.filter(id=species_id).count() == 1:
            organism = Organism.objects.get(id=species_id)
        else:
            print("Organism with ID %s does not appear to be in COG/eggNOG, so cannot be imported." % species_id)
            sys.exit(1)
        
        
        ## Get mnxref_dict - value is reaction object
        
        print("Creating MNXRef synonym dictionary ...")
        mnxref_list = Reactionsynonym.objects.select_related().all()
        mnxref_dict = {}

        
        for synonym in mnxref_list:
            
            mnxref_dict[synonym.synonym] = synonym.reaction
            
        
        ### Find all COG annotations for genes in this species
        
        ## Get gene_cog_dict (using Network species ID)
        
        print("Preparing gene and enzyme dictionaries ...")
        
        gene_cog_list = Gene.objects.filter(organism_id = species_id).exclude(cogs=None).prefetch_related()        
        gene_cog_dict = {}
        gene_cog_dict_cas = {}
    
        
        for gene in gene_cog_list:
            
            
            
            gene_cog_dict[gene.locus_tag] = gene.cogs.all()
            
            cog_list = []
            for cog in gene.cogs.all():
                cog_list.append(cog.id)
            
            gene_cog_dict_cas[gene.locus_tag] = cog_list
            
            #print("%s - %s" % (gene.locus_tag, ",".join(cog_list)))
        
        ### Add cogzymes to reaction nodes
        ### Find all genes in model that do not have COG assignments (and enzymes that contain them)
        
        genes_not_found_dict = {}
        enzymes_not_found_dict = {}
        rxns_unfound_gpr = []
        rxns_limited_gpr = []
        for rxn_node in model_rxn_list:
            
            genes_not_found, enzymes_not_found = extract_cogzymes_from_enzymes(rxn_node, gene_cog_dict_cas)
        
            for gene in genes_not_found:
                dict_append(genes_not_found_dict,gene,rxn_node["id"])
            
            for enzyme in enzymes_not_found:
                dict_append(enzymes_not_found_dict,enzyme,rxn_node["id"])
            
            if (len(rxn_node["gpr"]) > 0):
                if len(rxn_node["cogzymes"]) == 0:
                    rxns_unfound_gpr.append(rxn_node)
                else:
                    rxns_limited_gpr.append(rxn_node)
        
        
        ## Print genes, enzymes and reactions with limited COGs
        
        lf.write("\nGenes without COGs:\n")
        for gene in genes_not_found_dict:
            lf.write("Gene: %s, reactions: %s" % (gene, ",".join(genes_not_found_dict[gene])))
            
        lf.write("\nEnzymes containing those genes:\n")
        for enzyme in enzymes_not_found_dict:
            lf.write("Gene: %s, reactions: %s" % (enzyme, ",".join(enzymes_not_found_dict[enzyme])))
        
        lf.write("\nReactions with GPRs, but without an assigned cogzyme:\n")
        for reaction in rxns_unfound_gpr:
            lf.write("%s, GPR '%s'" % (reaction["id"], reaction["gpr"]))
        
        lf.write("\nReactions with GPRs, but with limited cogzyme coverage:\n")
        for reaction in rxns_limited_gpr:
            lf.write("%s, GPR '%s'" % (reaction["id"], reaction["gpr"]))
        
        lf.close()
        
        
        ## Check whether metabolic model exists and if so delete all relevant data to update database
        
        if Metabolicmodel.objects.filter(id=model_id).count() == 1:
            ## Delete all previous data about this model, except reaction synonyms
            
            print("This metabolic model already exists, deleting old version ...")
            
            Enzyme.objects.filter(metabolicmodel__id=model_id).delete()
            Modelrxn.objects.filter(metabolicmodel__id=model_id).delete()
            Cogzyme.objects.all().delete() ##!!!!!!!!! REMOVE SOON!!!!!
    
            ## Retrieve model itself
            
            metmodel = Metabolicmodel.objects.get(id=model_id)
        else:
            metmodel = Metabolicmodel(
                id = model_id,
                organism = organism
            ) 
            metmodel.save()
        
        print metmodel
        
        
        ## Create reaction dictionary for all relevant synonyms: key=synonym, value=reaction
        
        print("Creating synonym dictionary ...")
        
        reaction_dict = {}        
        rxn_synonyms = Reactionsynonym.objects.select_related().all()
        for rxn_synonym in rxn_synonyms:
            reaction_dict[rxn_synonym.synonym] = rxn_synonym.reaction
        
        ###! Cycle through reactions in model_rxn_list creating Modelrxn, enzyme and cogzyme entries and linking them up.
        
        rxn_not_found = []
        gene_not_in_cog = []
        
        print("Importing reactions ...")
        
        ## Initiate counter
        num_tot = len(model_rxn_list)
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()
        
        for rxn in model_rxn_list:
            ### Create Modelrxn
            
            ## If name is not in synonym list
            if rxn["id"] not in reaction_dict:
                
                rxn_not_found.append(rxn)
                
        
                ## Create new Reaction and give it an ID to distinguish it from other reactions
                
                reaction = Reaction(
                    name = rxn["id"],
                    mnx_id = rxn["id"] + "_" + model_id
                )
                reaction.save()
                mnx_reaction = reaction
                
                synsource = Reactionsynonymsource(
                    name = model_id
                )
                synsource.save()
                
                syn = Reactionsynonym(
                    synonym = rxn["id"],
                    source = synsource,
                    reaction = mnx_reaction
                )
                syn.save()
                
                reaction_dict[syn.synonym] = syn.reaction
                
            else:
                mnx_reaction = reaction_dict[rxn["id"]]
            
            
            modelrxn = Modelrxn(
                id = rxn["id"],
                metabolicmodel = metmodel,
                reaction = mnx_reaction
            )
            modelrxn.save()
            
            
            ### Create Enzymes and link to reactions, genes and metabolicmodel
            
            enzyme_and_cogs_list = []
            
            for enz in rxn["enzymes"]:
                ## Sort genes to ensure no replication of enzymes
                
                gene_list_sorted = sorted(enz.gene_list)
                enz_name = ",".join(gene_list_sorted)
                
                if Enzyme.objects.filter(name=enz_name).count() < 1:
                    ## Add enzyme (if does not exist) with name and metabolicmodel
                    
                    enzyme = Enzyme(
                        name = enz_name,
                        metabolicmodel = metmodel,
                    )
                    enzyme.save()
                    
                    ## Add gene relationships
                    
                    gene_mod_list = []
                    for gene_name in gene_list_sorted:
                        
                        cog_list = []
                        
                        if Gene.objects.filter(locus_tag=gene_name).count() == 1:
                            gene = Gene.objects.get(locus_tag=gene_name)
                            for cog in gene.cogs.all().order_by("id"):
                                cog_list.append(cog)
                        else:
                            ## Gene not in COG
                            gene_not_in_cog.append(gene_name)
                            gene = Gene(
                                locus_tag=gene_name,
                                organism=organism,
                            )
                            gene.save()
                        gene_mod_list.append(gene)
                        
                    enzyme.genes.add(*gene_mod_list)
                else:
                    enzyme = Enzyme.objects.get(name=enz_name)
                        
                ## Add reaction relationship
                
                ##! Could move to end and do with list of mnx_reactions?
                enzyme.reactions.add(mnx_reaction)
                
                
                ### Create/update COGzyme for this enzyme
                
                enzyme_and_cogs_list.append([enzyme, cog_list])
                
                
                ##Create cogzyme name
                cog_name_list = []
                for cog in cog_list:
                    cog_name_list.append(cog.id)
                cog_name_list.sort()
                cogzyme_name = ",".join(cog_name_list)
                
                if len(cogzyme_name) > 0:
                    if Cogzyme.objects.filter(name=cogzyme_name).count() == 1:
                        cogzyme = Cogzyme.objects.get(name=cogzyme_name)
                    else:
                        cogzyme = Cogzyme(
                            name=cogzyme_name,
                            )
                        cogzyme.save()
                        
                        if len(cog_list) == 0:
                            print rxn["id"]
                            print enzyme
                            print cog_list
                            sys.exit(1)
                        
                        cogzyme.cogs.add(*cog_list)
                    
                    cogzyme.enzymes.add(enzyme)
                 
            ## Counter progress
            num_done += 1
            if ((100 * num_done) / num_tot) > next_progress:
                sys.stdout.write("\r - %d %%" % next_progress)
                sys.stdout.flush()
                next_progress += 1
        
        ## Finish counter
        sys.stdout.write("\r - 100 %\n")
        sys.stdout.flush()