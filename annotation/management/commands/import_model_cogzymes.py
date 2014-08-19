from django.core.management.base import BaseCommand, CommandError
from annotation.models import Compartment, Reaction, Evidence, Catalyst, EC,\
                                EC_Reaction, Source, Reaction_synonym,\
                                Model_reaction, Model_metabolite,\
                                Metabolite_synonym, Metabolite,\
                                Reaction_group, Method, Mapping
from cogzymes.models import Organism, Gene, Cog, Cogzyme, Enzyme, Enzyme_type
from annotation.management.commands.model_integration_tools import get_synonym_met_db, get_subsynonyms
from myutils.general.gene_parser import gene_parser
from myutils.general.utils import loop_counter, dict_append
from myutils.SBML.import_SBML import import_SBML_to_bipartite as import_sbml
from myutils.django.utils import get_model_dictionary
from myutils.networkx.utils import nodes
import sys, re
from copy import deepcopy
from bioservices import UniProt


def test_mapped_rxns_by_metprint(source_name):
    """
    Look at all mapped model_reactions to see whether their metprint fits the mapped db_reaction metprint.
    """

    db_rxns_fully_mapped = Reaction.objects\
                    .filter(stoichiometry__metabolite__model_metabolite__source__name = source_name)\
                    .exclude(stoichiometry__metabolite__model_metabolite__isnull=True).distinct()\
                    .values_list('name', flat=True)

    
    ## For each mapped model_reaction
    
    num_full_mapped = 0
    num_full_not_mapped = 0
    num_incomplete = 0
    
#     counter = loop_counter(Model_reaction.objects.filter(db_reaction__isnull=False, source__name=source_name).count(), "Looking for correct mappings ...")
    
    print("Testing {} reactions ...".format(Model_reaction.objects.filter(db_reaction__isnull=False, source__name=source_name).count()))
    
    for model_rxn in Model_reaction.objects.filter(db_reaction__isnull=False, source__name=source_name):
        
#         counter.step()
        
        subs, prod, model_complete = model_rxn.metprint()
    
        ## does it have complete metprint?
        if model_complete:
            model_metprint = frozenset([subs,prod])
            
            ## does it match to mapped db_reaction metprint?
            
            db_reaction = model_rxn.db_reaction
            subs_fset, prod_fset, db_complete = db_reaction.metprint()
            
            if db_complete:
            
                db_metprint = frozenset([subs_fset, prod_fset])
                
#                 print model_metprint
#                 print db_metprint
#                 print("")
                
                if model_metprint == db_metprint:
                    num_full_mapped += 1
                
                else:
                    ## if not, is db_reaction fully metmapped to model? 
                    
                    if db_reaction.name in db_rxns_fully_mapped:
                        num_full_not_mapped += 1
                        print("incorrect: {:30} - {:30}".format(model_rxn.model_id, db_reaction.name))
                        
                    else:
                        num_incomplete += 1
            
            else:
                ## DB Reaction does not have full stoichiometry
                num_incomplete += 1
        else:
            num_incomplete += 1
                    
#     counter.stop()
    
    print("{} reactions mapped correctly, {} mapped incorrectly (incomplete metprints for {} reactions)"\
                    .format(num_full_mapped, num_full_not_mapped, num_incomplete))
                              
def map_reaction_metprints(source_name):
    """
    Look for model_reactions that do not map by name/id to db_metabolites and look for metabolite equivalence.
    """
    
    ## Find all db_reactions which fully map to model_metabolitesfrom the source input model
    
    db_reactions = Reaction.objects\
                    .filter(stoichiometry__metabolite__model_metabolite__source__name = source_name)\
                    .exclude(stoichiometry__metabolite__model_metabolite__isnull=True).distinct()
    
    
    ## Create a metprint dictionary of all fully mapped db_reactions
    
    db_rxn_dict_app = {}
    num_mapped_db_rxns = 0
    counter = loop_counter(len(db_reactions), "Preparing db_reaction dictionary ...")
    for db_rxn in db_reactions:
        counter.step()
        subs, prod, complete = db_rxn.metprint()
        if complete:
            dict_append(db_rxn_dict_app,frozenset([subs,prod]),db_rxn)
            num_mapped_db_rxns += 1
    counter.stop()
    
    
    ## Remove duplicate metprints
    
    db_rxn_dict = {}
    for metprint in db_rxn_dict_app:
        if len(db_rxn_dict_app[metprint]) == 1:
            db_rxn_dict[metprint] = db_rxn_dict_app[metprint][0] 
    
    num_db_dup_metprints = len(db_rxn_dict_app) - len(db_rxn_dict)
    print("{} fully mapped reactions in the DB:".format(num_mapped_db_rxns))
    print(" - {} duplicate metprints in the DB".format(num_db_dup_metprints))
    
    ## Find all model_reactions that fully map to db_metabolites and test against the metprint dictionary
    
    model_rxn_dict_app = {}
    num_mapped_model_rxns = 0
    for model_rxn in Model_reaction.objects.filter(db_reaction__isnull=True, source__name=source_name):
        subs, prod, complete = model_rxn.metprint()
        
#         print model_rxn.model_id
#         print subs
#         print prod
#         print complete
#         print("")
        
        if complete:
            model_rxn_metprint = frozenset([subs,prod])
            dict_append(model_rxn_dict_app,model_rxn_metprint,model_rxn)
            num_mapped_model_rxns += 1
            
    
    ## Remove duplicate metprints
    
    model_rxn_dict = {}
    print("\nMapped model reactions:\n")
    for metprint in model_rxn_dict_app:
        if len(model_rxn_dict_app[metprint]) == 1:
            model_rxn_dict[metprint] = model_rxn_dict_app[metprint][0]
#             print(" - {}".format(model_rxn_dict[metprint].id))
#             print metprint
#             print("") 
             
    num_model_dup_metprints = len(model_rxn_dict_app) - len(model_rxn_dict)
    print("{} fully mapped reactions in the model:".format(num_mapped_model_rxns))
    print(" - {} duplicate metprints in the model".format(num_model_dup_metprints))
    
    ## Compare metprints for equivalents and assign db_reactions to model_reactions
    
    num_mapped = 0
    
    for metprint in model_rxn_dict:
        if metprint in db_rxn_dict:
            model_rxn = model_rxn_dict[metprint]
            db_rxn = db_rxn_dict[metprint]
            model_rxn.db_reaction = db_rxn
            model_rxn.save()
            num_mapped += 1
    
    print("{} model reactions mapped to DB reactions using metprints.".format(num_mapped)) 
    
def maps_to_db_met(syn_met_dict, model_met):
    """
    If unambiguous DB metabolite can be found for model metabolite, add link in model_metabolite entry.
    """
    
    model_syns = [model_met.model_id.lower(), model_met.name.lower()]
    
    all_synonyms = deepcopy(model_syns)
    
    for synonym in model_syns:
        subsynonyms = get_subsynonyms(synonym)
        for syn in subsynonyms:
            all_synonyms.append(syn)
    
    all_synonyms = list(set(all_synonyms))
    
    mappings = []
    for synonym in all_synonyms:
        if synonym in syn_met_dict:
            mappings.append(syn_met_dict[synonym])
    
    mappings = list(set(mappings))
    
    dup_mappings = []
    
    if len(mappings) == 1:
        model_met.db_metabolite = mappings[0]
        map_status = True
    else:
#         print("\nMapping failed for metabolite {}:".format(model_met.model_id))
#         print(" - ID: {}".format(model_met.model_id.lower()))
#         print(" - name: {}".format(model_met.name.lower()))
#         print(" - Mappings:")
#         for mapping in mappings:
#             print("   - {}".format(mapping))
#         print(" - Synonyms:")
#         for synonym in all_synonyms:
#             print("   - {}".format(synonym))
        
        if len(mappings) > 1:
            dup_mappings = mappings

        map_status = False
        
    return model_met, map_status, dup_mappings

def maps_to_db_rxn(syn_rxn_dict, model_rxn):
    """If unambiguous DB metabolite can be found for model metabolite, add link in model_metabolite entry."""
    
    model_syns = [model_rxn.model_id.lower(), model_rxn.name.lower()]
    
    all_synonyms = deepcopy(model_syns)
    
    for synonym in model_syns:
        subsynonyms = get_subsynonyms(synonym)
        for syn in subsynonyms:
            all_synonyms.append(syn)
    
    all_synonyms = list(set(all_synonyms))
    
    mappings = []
    for synonym in all_synonyms:
        if synonym in syn_rxn_dict:
            mappings.append(syn_rxn_dict[synonym])
    
    mappings = list(set(mappings))
    
    dup_mappings = []
    
    if len(mappings) == 1:
        model_rxn.db_reaction = mappings[0]
        map_status = True
    else:
#         print("\nMapping failed for reaction {}:".format(model_rxn.model_id))
#         print(" - ID: {}".format(model_rxn.model_id.lower()))
#         print(" - name: {}".format(model_rxn.name.lower()))
#         print(" - Mappings:")
#         for mapping in mappings:
#             print("   - {}".format(mapping))
#         print(" - Synonyms:")
#         for synonym in all_synonyms:
#             print("   - {}".format(synonym))
         
        if len(mappings) > 1:
            dup_mappings = mappings

        map_status = False
        
    return model_rxn, map_status, dup_mappings

def get_gene_locus_from_uniprot_id(uniprot_id):
    """ Retrieve gene locus from Uniprot ID."""
    
    u = UniProt(verbose=True)
    gene = u.mapping(fr='ACC',to='KEGG_ID',query=uniprot_id)[uniprot_id][0]
    gene_locus_tag = gene.split(":")[-1]

    return gene_locus_tag

class Command(BaseCommand):
    
    help = 'Populate Model_reaction and Model_metabolite tables from input SBML model.'
        
    def handle(self, *args, **options):
        
        """Model_reaction and Model_metabolite tables."""
        
        try:
            model_file_in = args[0]
        except:
            model_file_in = '/Users/wbryant/work/cogzymes/models/ECO_iJO1366.xml'
            print("Using default model ...")
        
        if len(args) == 2:
            if args[1] == 'add_cogzymes':
                add_cogzymes = True
                print("Import will include adding cogzymes ...")
        else:
            add_cogzymes = False


        ## Import model data using NetworkX
        
        G = import_sbml(model_file_in, add_cogzymes)
        
        
        
        
        ## If COGzymes are being imported, make preparations
        
        if add_cogzymes:
            
            ## Check / add 'type' for Enzymes
            
            ez_type_type = 'Metabolic Model'
            ez_type_description = 'Imported from a metabolic model.'
            
            try:
                ez_type = Enzyme_type.objects.get(type=ez_type_type)
            except:
                ez_type = Enzyme_type(
                    type = ez_type_type,
                    description = ez_type_description
                )
                try:
                    ez_type.save()
                except:
                    print('Enzyme type not created successfully, exiting ...')
                    sys.exit(1)
    
            
            ## Is species taxonomy ID specified?  If importing cogzymes this must be specified
            
            if G.species_id == 'Unknown':
                print("Species ID was not specified in SBML model ID.  Please use format 'model_id - taxonomy_id' for the model ID.")
                sys.exit(1)
            else:
                print("Species taxonomy ID is {} ...".format(G.species_id))        

        
            ## Is organism available in COG?
        
            taxonomy_id = G.species_id
            try:
                organism = Organism.objects.get(taxonomy_id=taxonomy_id)
                
                
                ## If available, get list of gene loci
                
                gene_locus_list = Gene.objects.filter(organism=organism).values_list('locus_tag', flat=True)
                
            except:
                print("Organism with ID {} does not appear to be in COG/eggNOG, so cannot be imported.".format(taxonomy_id))
                sys.exit(1)
            
        
            ## Get dictionary of cog terms with gene locus as key for this organism
        
            counter = loop_counter(Gene.objects.filter(organism=organism).count(),"Getting COGs and genes for all organism gene loci ...")
            
            locus_cog_dict = {}
            locus_gene_dict = {}
            for gene in Gene.objects.filter(organism=organism).prefetch_related():
                counter.step()
                cog_list = []
                for cog in Cog.objects.filter(gene=gene):
                    cog_list.append(cog)
                
                locus_cog_dict[gene.locus_tag] = cog_list
                
                locus_gene_dict[gene.locus_tag] = gene
        
            counter.stop()
            
            
            ## Create cog/cogzyme dictionary
            
            name_cogzyme_dict = get_model_dictionary(Cogzyme, 'name')
            #name_cog_dict = get_model_dictionary(Cog, 'name')
            
       
        ## Get dictionary of unambiguous synonyms to relate model metabolites to DB metabolites.
        
        counter = loop_counter(Metabolite_synonym.objects.all().count(),'Getting metabolite synonyms ...')
        synonym_db_met_dict = {}
        for syn in Metabolite_synonym.objects.all().prefetch_related('metabolite'):
            counter.step()
            synonym_db_met_dict[syn.synonym.lower()] = syn.metabolite
        counter.stop()


        ## Get dictionary of unambiguous synonyms to relate model reactions to DB reactions.
        
        counter = loop_counter(Reaction_synonym.objects.all().count(),'Getting reaction synonyms ...')
        synonym_db_rxn_dict = {}
        for syn in Reaction_synonym.objects.all().prefetch_related('reaction'):
            counter.step()
            synonym_db_rxn_dict[syn.synonym.lower()] = syn.reaction
        counter.stop()

        
        ## Create source
        
        source_name = G.model_id
        print("Source name is: {}".format(source_name))
        try:
            source = Source.objects.get(name=source_name)
            if not source.organism:
                source.organism = organism
                source.save()
        except:
            source = Source(
                name=source_name,
                organism=organism
            )
            source.save()
        

        ## Remove previous information from this source
        
        print("Deleting previous entries for this model (curated model mappings will need to be re-added ...")
        
        Model_metabolite.objects.filter(source=source, curated_db_link=False).delete()
        Model_reaction.objects.filter(source=source, curated_db_link=False).delete()
        Enzyme.objects.filter(source=source).delete()
        
        met_dict = {}
        rxn_dict = {}
        
        counter = loop_counter(len(G), "Running through nodes for input into DB ...")
        
        num_not_mapped = 0
        num_mapped = 0
        
        num_rxn_not_mapped = 0
        num_rxn_mapped = 0
        
        ## For mappings to multiple metabolites, store all mappings in dict, along with 
        ## metabolite model_id.  Then eliminate all duplicate mappings across the model and
        ## see whether any further metabolites can be uniquely mapped.
        dup_mappings_dict = {}
        
        dup_rxn_mappings_dict = {}
        
        if add_cogzymes:
            name_enzyme_dict = {}
            genes_not_found = []
        
        for idx in G.nodes():
            counter.step()
            node = G.node[idx]
            if node['type'] == 'metabolite':
                
                compartment_id = node['id'][-1:]
                if compartment_id == 'e':
                    compartment = Compartment.objects.get(id='MNXC2')
                elif compartment_id == 'p':
                    compartment = Compartment.objects.get(id='MNXC19')
                else:
                    compartment = Compartment.objects.get(id='MNXC3')
                    
                model_id = re.sub('_[a-zA-Z]$','',node['id'])
                model_id = re.sub('^M_','',model_id)
                
                met = Model_metabolite(
                        model_id = model_id,
                        name = node['name'],
                        compartment = compartment,
                        source = source,
                        curated_db_link = False
                )
                
                
                ## Can the metabolite be unambiguously mapped to the DB?
                
                met, map_status, dup_mappings = maps_to_db_met(synonym_db_met_dict,met)
                for dup_mapping in dup_mappings:
                    dict_append(dup_mappings_dict, dup_mapping.id, node['id'])        
                if map_status == False:
                    num_not_mapped += 1
                else:
                    num_mapped += 1
                    
                
                ## Save model metabolite and store for addition to reactions 
                
                met.save()
                met_dict[node['id']] = met
            
            else:
                ## Node is a reaction, so import as such
                
                rxn_id = re.sub('^R_','',node['id'])
                
                rxn = Model_reaction(
                        model_id = rxn_id,
                        name = node['name'],
                        gpr = node['gpr'],
                        source = source,
                        curated_db_link = False
                )

                
                ## Can the reaction be unambiguously mapped to the DB?
                
                rxn, map_status, dup_mappings = maps_to_db_rxn(synonym_db_rxn_dict,rxn)
                for dup_mapping in dup_mappings:
                    dict_append(dup_rxn_mappings_dict, dup_mapping.id, node['id'])        
                if map_status == False:
                    num_rxn_not_mapped += 1
                else:
                    num_rxn_mapped += 1
                
                
                ## Save model reaction and make available in a dictionary
                
                try:
                    rxn.save()
                except:
                    print len(rxn.gpr)
                    print rxn.gpr
                    print rxn.name
                    print rxn.model_id
                    sys.exit(1)
                rxn_dict[node['id']] = rxn
                
                
                ### If adding cogzymes, do it here
                
                if add_cogzymes:
                    
                    ## Find cogzymes for this reaction
                    
                    for enzyme_name in node['enzymelist']:

                        genes = enzyme_name.split(",")
                        
                        ## List of COGs represented in the enzyme
                        cog_list = []
                        cog_name_list = []
                        valid_cogzyme = True
                        
                        for gene_locus in genes:
                            if gene_locus in gene_locus_list:
                                ## If gene is present according to COG, append to COG list
                                
                                for cog in locus_cog_dict[gene_locus]:
                                    cog_list.append(cog)
                                    cog_name_list.append(cog.name)
                                
                            else:
                                ## COGzyme cannot be formed because of a non-COG gene
                                valid_cogzyme = False
                                
                                genes_not_found.append(gene_locus)
                        
                        
                        ## Do not proceed with import of enzyme if the COGzyme cannot be identified
                        
                        if valid_cogzyme:
                            ## If enzyme does not exist, add it to DB
                        
                            if enzyme_name in name_enzyme_dict:
                                enzyme = name_enzyme_dict[enzyme_name]
                            else:
                                enzyme = Enzyme(
                                    name = enzyme_name,
                                    source = source,
                                    type = ez_type
                                )
                                enzyme.save()
                                name_enzyme_dict[enzyme_name] = enzyme


                            ## Add reaction and genes to enzyme
                            
                            enzyme.reactions.add(rxn)
                            
                            for gene_locus in genes:
                                enzyme.genes.add(locus_gene_dict[gene_locus])

                            
                            ## Create cogzyme name and check whether it is in the COGzyme table
                            
                            cog_name_list = sorted(list(set(cog_name_list)))
                            
                            cogzyme_name = ",".join(cog_name_list)
                            
                            if cogzyme_name in name_cogzyme_dict:
                                cogzyme = name_cogzyme_dict[cogzyme_name]
                            else:

                                if len(cogzyme_name) > 255:
                                    full_name = deepcopy(cogzyme_name)
                                    cogzyme_name = cogzyme_name[0:254]
                                                                    
                                cogzyme = Cogzyme(
                                    name = cogzyme_name,
                                )
                                
                                try:
                                    cogzyme.save()
                                except:
                                    print("Long name uniqueness error for name '{}'.".format(full_name))
                                    continue
                                
                                for cog in cog_list:
                                    cogzyme.cogs.add(cog)
                                
                                name_cogzyme_dict[cogzyme_name] = cogzyme
                                
                            cogzyme.enzymes.add(enzyme)
                
        counter.stop()
        
        counter = loop_counter(len(dup_mappings_dict),"Eliminating duplicate metabolite mappings ...")
        
        for db_met_id in dup_mappings_dict:
            counter.step()
            if len(dup_mappings_dict[db_met_id]) == 1:
                ## Only one model metabolite is referred to by this DB metabolite - can be mapped
                 
#                 print db_met_id
#                 print dup_mappings_dict[db_met_id][0]
#                 print met_dict[dup_mappings_dict[db_met_id][0]]
                
                model_met = met_dict[dup_mappings_dict[db_met_id][0]]
                
                db_met = Metabolite.objects.get(id=db_met_id)
                
                model_met.db_metabolite = db_met
                
                model_met.save()
                
                num_mapped += 1
                num_not_mapped -= 1
        
        counter.stop()
        
        print("{} metabolites were mapped and {} metabolites were not mapped.".format(num_mapped, num_not_mapped))
        
        
        ## Eliminate reaction duplicates and find further mappings
        
        counter = loop_counter(len(dup_rxn_mappings_dict),"Eliminating duplicate reaction mappings ...")
        
        for db_rxn_id in dup_rxn_mappings_dict:
            counter.step()
            if len(dup_rxn_mappings_dict[db_rxn_id]) == 1:
                ## Only one model reaction is referred to by this DB reaction - can be mapped
                 
                model_rxn = rxn_dict[dup_rxn_mappings_dict[db_rxn_id][0]]
                
                db_rxn = Reaction.objects.get(id=db_rxn_id)
                
                model_rxn.db_reaction = db_rxn
                
                model_rxn.save()
                
                num_rxn_mapped += 1
                num_rxn_not_mapped -= 1
        
        counter.stop()
        
        print("{} reactions were mapped and {} reactions were not mapped.".format(num_rxn_mapped, num_rxn_not_mapped))
  
        
        ## Once all metabolites and reactions are imported, add links between reactions and metabolites
        
        print('Adding links between reactions and metabolites ...') 
        
        for node, idx in nodes(G, 'reaction'):
            rxn = rxn_dict[node['id']]
            
            met_idx_list = []
            subs_list = []
            prod_list = []
            
            for edge in G.edges(idx):
                met_idx_list.append(edge[1])
                prod_list.append(edge[1])
                            
            for edge in G.in_edges(idx):
                met_idx_list.append(edge[0])
                subs_list.append(edge[0])
                        
            for idx in met_idx_list:
                met = met_dict[G.node[idx]['id']]    
                rxn.metabolites.add(met)
                
            for idx in prod_list:
                met = met_dict[G.node[idx]['id']]    
                rxn.products.add(met)
            
            for idx in subs_list:
                met = met_dict[G.node[idx]['id']]    
                rxn.substrates.add(met)

#             print rxn.name
#             print subs_list
#             print prod_list
#             print met_idx_list
#             print("")
            
            rxn.save()                
            
            
        ## Map reactions by metprints
        
        map_reaction_metprints(source_name)        
        
        
        ## Mapped reactions must also be added to Reaction Groups (method 'MNX', name=MNX_ID)
        
        try:
            method = Method.objects.get(name='MNX')
        except:
            method = Method(name='MNX')
            method.save()
        
        counter = loop_counter(Model_reaction.objects
            .filter(source=source, db_reaction__isnull=False).count(), 
            "Adding mapped reactions to Groups ...")
        
        for rxn in Model_reaction.objects.filter(
            source=source, 
            db_reaction__isnull=False):
            
            counter.step()
            

            try:
                group = Reaction_group.objects.filter(model_reaction__db_reaction=rxn.db_reaction).distinct()[0]
            except:
                group = Reaction_group(
                    name= "{} from {}".format(
                        rxn.db_reaction.name,
                        rxn.db_reaction.source.name
                    )
                )
                
                group.save()
                
            mapping = Mapping(
                reaction = rxn,
                group = group,
                method = method
            )
            
            mapping.save()
        
        counter.stop()
 
        print("Completed model import.\n")
        
        genes_not_found = sorted(list(set(genes_not_found)))
        
        if add_cogzymes:
            print("Gene loci not found for cogzyme import:")
            for gene in genes_not_found:
                print(" - {}".format(gene))
        
        
        
           