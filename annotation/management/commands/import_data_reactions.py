from django.core.management.base import NoArgsCommand, CommandError
from annotation.models import Reaction, EC, EC_Reaction, Source, Reaction_synonym
import sys, re
from myutils.general.utils import loop_counter

def import_extra_seed_ids(seed_file):
    """
    Import full names from SEED reaction table.
    For some reason MetaNetX does not have the complete list of SEED synonyms - just IDs.
    """
    
    ###! Very inefficient!  Use single django lookups
    
    try:
        source = Source.objects.get(name='seed')
    except:
        print("SEED source could not be found ...")
        sys.exit(1)
    
    f_in = open(seed_file,'r')
    
    num_lines = 0
    for line in f_in:
        num_lines += 1
    
    f_in.close()
    
    f_in = open(seed_file,'r')
    
    
    counter = loop_counter(num_lines, "Getting additional synonyms for SEED ...")
    
    for line in f_in:
        
        counter.step()
        
        rows = line.split("\t")
        
        seed_id = rows[0]
        seed_name = rows[1]
        
        try:
            syn = Reaction_synonym.objects.get(synonym=seed_name)
#             print("Synonym '{}'({}) already exists ...".format(seed_name, syn.source))
        except:
            try:
                reaction = Reaction.objects.get(reaction_synonym__synonym=seed_id)
                
                new_syn = Reaction_synonym(
                    synonym = seed_name,
                    reaction = reaction,
                    source = source,
                    inferred = False 
                )
                
                new_syn.save()
                
            except:
#                 print("Reaction '{}, {}' could not be uniquely identified ...".format(seed_name, seed_id))
                pass
    
    counter.stop()
    
class Command(NoArgsCommand):
    
    help = 'Imports data to the Reaction table from the MNXRef downloaded xref file.'
        
    def handle(self, **options):
        
        relevant_sources = ["seed", "metacyc", "kegg", "chebi", "brenda", "bigg"]
        
        source_precedence = {}
        
        source_precedence["chebi"] = 4.5
        source_precedence["metacyc"] = 2
        source_precedence["bigg"] = 3
        source_precedence["seed"] = 4
        source_precedence["kegg"] = 5
        source_precedence["brenda"] = 6
        
        source_id = 'metanetx'
        
        sources = Source.objects.all()
        source_dict = {}
        for source in sources:
            source_dict[source.name] = source
        
        for rel_source in relevant_sources:
            if rel_source not in source_dict:
                source = Source(
                    name = rel_source
                )
                source.save()
                source_dict[rel_source] = source
        
        
        if source_id in source_dict:
            rxn_source = source_dict[source_id]
        else:
            rxn_source = Source(name = source_id)
            rxn_source.save()  
        
        
        Reaction.objects.filter(source=rxn_source).delete()
        EC_Reaction.objects.filter(source=rxn_source).delete()
        EC.objects.filter(source=rxn_source).delete()
        #EC.objects.all().delete()
        
        xref_file = "/Users/wbryant/work/BTH/data/metanetx/reac_xref.tsv"
        prop_file = "/Users/wbryant/work/BTH/data/metanetx/reac_prop.tsv"
        
        
        f_in = open(xref_file, 'r')
        
        num_lines = 0
        for line in f_in:
            num_lines += 1
        f_in.close()
        f_in = open(xref_file, 'r')
        
        print 'Populating Reaction table ...'
        #Initiate counter
        counter = loop_counter(num_lines)
        
        reaction_dict = {}
        synonym_dict = {}
        syn_source_dict = {}
        dup_synonym_dict = {}
        
        for line in f_in:
            counter.step()
            
            if line[0] != "#":
                line_old = line[:]
                line = line.strip().split('\t')
                
                synonym_source, synonym = line[0].split(":",1)
                
                ## If synonym from relevant source, and name not already used, add
                if synonym_source in relevant_sources:
                    
                    name = line[1]
                    
                    if name in reaction_dict:
                        reaction = reaction_dict[name]
                    else:
                        reaction = Reaction(
                            name = name,
                            source=rxn_source
                        )
                        reaction.save()
                        reaction_dict[name] = reaction
                        
                        reaction_synonym = Reaction_synonym(
                            synonym=name,
                            reaction=reaction,
                            source=rxn_source
                        )
                        reaction_synonym.save()
                    
                    for_saving = False
                    
                    if synonym in synonym_dict:
                        ## Name already found so check whether the new one has precedence
                        old_syn = synonym_dict[synonym]
                        
                        if old_syn.reaction.pk != reaction.pk:
                            ## If the reactions are the same, do not do anything 

                            old_source = syn_source_dict[old_syn]

                            if source_precedence[synonym_source] < source_precedence[old_source]:
                                for_saving = True
                                old_syn.delete()
                                dup_synonym_dict.pop(synonym, None)
                            elif synonym_source == old_source:
                                ## If the same source, add to duplicates
                                for_saving = True 
                                if synonym in dup_synonym_dict:
                                    if reaction not in dup_synonym_dict[synonym]: 
                                        dup_synonym_dict[synonym].append(reaction)
                                else:
                                    old_rxn = old_syn.reaction
                                    dup_synonym_dict[synonym] = [old_rxn, reaction]
                    else:
                        for_saving = True
                        
                    if for_saving:
                        rxn_syn = Reaction_synonym(
                            synonym = synonym,
                            reaction = reaction,
                            source = source_dict[synonym_source]
                        )
                        try:
                            rxn_syn.save()
                        except:
                            #print("Long name not saved to DB ...")
                            pass
                        syn_source_dict[rxn_syn] = synonym_source
                        synonym_dict[synonym] = rxn_syn
                    
        
        f_in.close()
        counter.stop()
        
        
        ## Import EC relationships from MNXRef (reac_prop.tsv)
        
        f_in = open(prop_file, 'r')
        
        num_lines = 0
        for line in f_in:
            num_lines += 1
        f_in.close()
        f_in = open(prop_file, 'r')
        
        print 'Populating EC table ...'
        counter2 = loop_counter(num_lines)
        
        for line in f_in:
            counter2.step()
            
            line_old = line[:]
            line = line.strip().split('\t')
            valid_line = False
            if line[0][0] != '#':
                valid_line = True
            
            if valid_line:
                name = line[0]
                #print id
                valid_reaction = True
                try:
                    reaction = Reaction.objects.get(name=name)
                except:
                    valid_reaction = False
                
                if valid_reaction:
                    ecs = line[4]
                    if len(ecs) > 0:
                        ec_nums = ecs.strip().split(';')
                        for ec_num in ec_nums:
                            
                            num_periods = ec_num.count('.')
                    
                            periods_needed = 3 - num_periods
                    
                            for i in range(0,periods_needed):
                                ec_num += '.-'
                            
                            try:
                                ec = EC.objects.get(number=ec_num)
                            except:
                                ec = EC(
                                    number = ec_num,
                                    source = rxn_source
                                )
                                ec.save()
                            
                            #Add link between EC and reaction
                            ec_reaction = EC_Reaction(
                                ec = ec,
                                reaction = reaction,
                                source = rxn_source
                            )
                            ec_reaction.save()
                            
        
        f_in.close()
        counter2.stop()
        
        import_extra_seed_ids('/Users/wbryant/work/BTH/data/SEED/rxn_table.csv')
        