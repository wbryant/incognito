from django.core.management.base import BaseCommand, CommandError
from cogzymes.models import Enzyme, Cogzyme, Gene, Cog
from myutils.general.utils import loop_counter
import sys, os, re
import cogzymes


class Command(BaseCommand):
    
    help = 'Migrate m2m relation between Cogzyme and Enzyme to FK relationship, since each enzyme only has 1 cogzyme'
        
    def handle(self, *args, **options):
        
        """ COMMAND DESCRIPTION
            
        """ 
        
        current_models = Source.objects.filter()
        
        gene_locus_list = Gene.objects.filter(organism__in = current_models).values_list('locus_tag', flat=True)
        
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
    
    
                