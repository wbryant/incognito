from django.core.management.base import NoArgsCommand, CommandError
from annotation.models import Reaction, Evidence, Catalyst, Enzyme, Gene, EC, EC_Reaction, Source, Reaction_synonym
from myutils.general.gene_parser import gene_parser
from myutils.general.utils import loop_counter
import sys, re

class Command(NoArgsCommand):
    
    help = 'Imports data to the Enzyme, Catalyst and Evidence tables from the downloaded iAH991 reaction table.'
        
    def handle(self, **options):
        
        """N.B. does not import metabolite data!"""
        
        ## Create Source
        source_name = "iAH991"
        
        try:
            source = Source.objects.get(name=source_name)
            source.delete()
        except:
            pass
            
        source = Source(name=source_name)
        source.save()
        

#         Catalyst.objects.filter(evidence__source=source).delete()
#         Evidence.objects.filter(source=source).delete()
        Enzyme.objects.filter(source=source).delete()
#         Reaction.objects.filter(source=source).delete()
#         EC.objects.filter(source=source).delete()
#         EC_Reaction.objects.filter(source=source).delete()
        
        #Enzymes (and link to genes)
        
        #Enzyme link to reactions
        
        f_in = open('/Users/wbryant/work/BTH/data/iAH991/iAH991_reactions.csv', 'r')
        #Populate: iAH991, Catalyst - and use EC Numbers to add to EC/reaction relationship.
        
        num_lines = 0
        for line in f_in:
            num_lines += 1
        f_in.close()
        
        
        f_in = open('/Users/wbryant/work/BTH/data/iAH991/iAH991_reactions.csv', 'r')
        
        print("Preparing dictionaries ...")
        
        #create BiGG and SEED dictionaries from Reaction to speed up table population
        bigg_rxn_dict = {}
        seed_rxn_dict = {}
        
        for synonym in Reaction_synonym.objects.filter(source__name="bigg"):
            bigg_rxn_dict[synonym.synonym] = synonym.reaction
        for synonym in Reaction_synonym.objects.filter(source__name="seed"):
            seed_rxn_dict[synonym.synonym] = synonym.reaction
        
        
        #Record number of reactions absent in MNXRef to be added to Reaction table
        num_mnx_absent = 0
        num_seed_found = 0
        num_bigg_found = 0
        
        gene_not_found_list = []
#         source_id = 'iAH991'
#         
#         if source_id in Source.objects.all().values_list("name", flat=True):
#             source = Source.objects.get(name=source_id)
#         else:
#             source = Source(name=source_id)
#             source.save()
        
        source_seed = Source.objects.get(name="seed")
        source_bigg = Source.objects.get(name="bigg")
        
        counter = loop_counter(num_lines, 'Populating iAH991, Enzyme and Catalyst table ...')               

        for line in f_in:
            
            counter.step()
            
            line = line.split('\t')
            #print line
            
            seed_id = line [0] #Capture in case BiGG ID is not found
            bigg_id = line[1]
            function = line[2]
            gpr = line[4]
            confidence = line[5]
            ec_field = line[6]
            #Ignore SEED IDs (use BiGG IDs), ignore EC numbers
            
            # Pull out enzymes
            enzymes_genes = gene_parser(gpr)
 
            if len(enzymes_genes) > 0:
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
                                gene_not_found_list.append(locus_tag)
                            if gene_found:
                                enzyme.genes.add(gene)
                        enzyme_list.append(enzyme)
            else:
                # No valid GPR, so is a gap
                
                if Enzyme.objects.filter(name='GAP').count() > 0:
                    enzyme_list = [Enzyme.objects.get(name='GAP')]
                else:
                    # Create gap 'enzyme'
                    enzyme = Enzyme(
                        name = 'GAP',
                        source = source
                    )
                    enzyme.save()
                    enzyme_list = [enzyme]
                
            
            ### Create foreign keys for Catalyst table
            
            ## Retrieve reaction
            if (len(bigg_id) > 0) & (bigg_id in bigg_rxn_dict):
                ## Find reaction by BiGG ID
                reaction = bigg_rxn_dict[bigg_id]
                num_bigg_found += 1
            elif (len(seed_id) > 0) & (seed_id in seed_rxn_dict):
                ## BiGG ID not found, therefore try SEED ID
                reaction = seed_rxn_dict[seed_id]
                
                ## Save BiGG ID
                if len(bigg_id) > 0:
                    bigg_synonym = Reaction_synonym(
                        synonym = bigg_id,
                        reaction = reaction,
                        source = source_bigg
                    )
                    bigg_synonym.save()
                
                bigg_rxn_dict[bigg_id] = reaction
                num_seed_found += 1
            else:
                ## Reaction not found in MNXRef, so add to reaction table
                num_mnx_absent += 1
                name = 'u_iah991%05d' % num_mnx_absent
                reaction = Reaction(
                    name = name,
                    source=source
                )
                reaction.save()
                
                if len(seed_id) > 0:
                    seed_synonym = Reaction_synonym(
                        synonym = seed_id,
                        reaction = reaction,
                        source = source_seed
                    )
                    seed_synonym.save()
                    seed_rxn_dict[seed_id] = reaction
                    
                if len(bigg_id) > 0:
                    bigg_synonym = Reaction_synonym(
                        synonym = bigg_id,
                        reaction = reaction,
                        source = source_bigg
                    )
                    bigg_synonym.save()
                    bigg_rxn_dict[bigg_id] = reaction
                
                
                
            ## Create score for evidence table and create evidence record
            score = float(confidence) / 4
            if score == 0:
                score = 0.1
            
            evidence = Evidence(
                source = source,
                score = score
            )
            evidence.save()
            
            ## Create catalyst instance for each enzyme in the model
            for enzyme in enzyme_list:
                catalyst = Catalyst(
                    enzyme = enzyme,
                    reaction = reaction,
                    evidence = evidence
                )
                catalyst.save()

            
            ### Add EC-to-Reaction relationships from iAH991
            ## Create EC dictionary for fast lookup
            ec_rxn_dict = {}
            for ec in EC.objects.all():
                ec_rxn_dict[ec.number] = ec
        
            if len(ec_field) > 1:
                ec_numbers = ec_field.strip().split(',')
                
                for ec_number in ec_numbers:
                    if ec in ec_rxn_dict:
                        ec = ec_rxn_dict[ec_number]
                    else:
                        ec = EC(
                            number = ec_number,
                            source = source
                        )
                        try:
                            ec.save()
                            ec_rxn_dict[ec_number] = ec
                        except:
                            print ec.number
                            sys.exit(1)
                    ec_reaction = EC_Reaction(
                        ec = ec,
                        reaction = reaction,
                        source = source
                    )
                    ec_reaction.save()

        counter.stop()

        
        gene_not_found_list = list(set(gene_not_found_list))
        print '\nThe following genes were not identified:'
        sys.stdout.write(' - ')
        
        for gene in gene_not_found_list:
            sys.stdout.write('%s, ' % gene)
        
        sys.stdout.flush()
        
        print '\n\niAH991 data imported ...'
        print ' - Number found by BiGG ID = %d' % num_bigg_found
        print ' - Number found by SEED ID = %d' % num_seed_found
        print ' - Number of new BiGG IDs found = %d' % num_mnx_absent
        f_in.close()
