# Get inclusive results for a list of COGs in a file

from django.core.management.base import NoArgsCommand, CommandError
from MODELS.models import *
from annotation.models import MTG_cog_result, Gene
import gapstats as GS
from operator import itemgetter
import sys, re, copy
from time import *

class Command(NoArgsCommand):
    
    help = 'Takes a COG and gets the inclusive and exlusive page of results from MTG, then puts them in the MTG_cog_result table.'
        
    def handle(self, **options):
        
	MTG_cog_result.objects.all().delete()
	
	# Get list of cogs for all BTH genes, if they have them.  Update the Gene table if so
	cog_gene_file = '/Users/wbryant/work/BTH/data/COG/BT_cog_associations.csv'
	f_in = open(cog_gene_file, 'r')
	
	list_of_locus = []
	num_lines = 0
	for line in f_in:
	    num_lines += 1
	    fields = line.split('\t')
	    
	    cog = fields[0]
	    gene_id = fields[1]
	    
	    locus_tag = re.sub('^.+\.','',gene_id)
	    #locus_tag = locus_tag_search.groups(1)
	    
	    
	    	    
	    print ';;%s;;' % locus_tag
	    print type(locus_tag)
	    
	    try:
		gene_back = Gene.objects.get(locus_tag=locus_tag)
		print ';;;;%s;;;;' % gene_back.locus_tag
	    except:
		pass
	    #list_of_locus.append(locus_tag)
	    
	    if num_lines > 9:
		break
	
	genes = Gene.objects.filter(locus_tag__contains='120')
	print '\n'
    
    
	for gene in genes:
	    print ';;;%s;;;' % gene.locus_tag
	    print type(gene.locus_tag)
	    gene_back = Gene.objects.get(locus_tag=gene.locus_tag)
	    #print ';;;;%s;;;;' % gene_back.locus_tag
	    
	