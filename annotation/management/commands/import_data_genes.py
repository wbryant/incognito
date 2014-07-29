from django.core.management.base import NoArgsCommand, CommandError
from annotation.models import Gene
import sys, re

class Command(NoArgsCommand):
    
    help = 'Imports data to the Gene table from the NCBI flatfile'
        
    def handle(self, **options):
        
        ## Get protein details from NCBI file to match ffpred
        
        prot_file = '/Users/wbryant/work/BTH/data/NCBI/prot_list.dat'
        f_in = open(prot_file, 'r')
        line = f_in.readline()
        
        prot_dict = {}
    
        while line:
            
            p_search = re.search('^VERSION.+GI:(\d+)',line)
            
            if p_search is not None:
                p_id = p_search.group(1)
            else:
                g_search = re.search('db_xref="GeneID:(\d+)',line)
                
                if g_search is not None:
                    g_id = g_search.group(1)
                    
                    prot_dict[g_id] = p_id
            line = f_in.readline()
        
        ## Run through genes for input into database
        
        print 'Populating Gene table ...'
        #Initiate counter
        num_tot = 4903
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()
    
    
        Gene.objects.all().delete()        
        f_in = open('/Users/wbryant/work/BTH/data/NCBI/gene_list.dat', 'r')
        line = f_in.readline()
        
        # Read gene_list and enter each gene into Gene table
        while line:
            new_gene = 0

            if len(line) > 0:
                #print line
                #print line[0]
                try:
                    int(line[0])
                    new_gene = 1
                except:
                    pass
            
            if (new_gene == 1):
                new_gene = 0
                # Read gene details in from file
                locus = re.search('[0-9]+\.\s(.+)$',line.strip()).group(1)
                name = re.search('^([^\[]+)\[',f_in.readline().strip()).group(1)
                line = f_in.readline().strip()
                try:
                    locus_tag = re.search('(BT\_[0-9]+)',line).group(1)
                except:
                    #print '\nNo BT number for gene %s, line:' % locus
                    #print ' - %s' % line
                    locus_tag = locus
                f_in.readline()
                line = f_in.readline().strip()
                try:
                    annotation = re.search('Annotation\:\s(.+)$',line).group(1)
                except:
                    #print '\nAnnotation not found for gene %s, line:' % locus
                    #print ' - %s' % line
                    #print ' - Trying next line ...'
                    line = f_in.readline().strip()
                    try:
                        annotation = re.search('Annotation\:\s(.+)$',line).group(1)
                    except:
                        #print '\nAnnotation not found for gene %s, line:' % locus
                        #print ' - %s' % line
                        annotation = ''
                line = f_in.readline().strip()
                try:
                    gi = int(re.search('ID\:\s(.+)$',line).group(1))
                except:
                    #print '\nGI not found for gene %s, line:' % locus
                    #print ' - %s' % line
                    gi = ''
                
                # Is there a known protein GI?
                if str(gi) in prot_dict:
                    protein_gi = prot_dict[str(gi)]
                    # Add gene to table
                    gene = Gene(
                            gi = gi,
                            locus = locus,
                            locus_tag = locus_tag,
                            name = name,
                            annotation = annotation,
                            protein_gi = protein_gi
                    )
                    try:
                        gene.save()
                    except:
                        print '\nGene not saved successfully: %s' % locus_tag
                        print '%s\t%s\t%s\t%s\t%s' % (gi, locus, locus_tag, name, annotation)
                else:
                    print 'Protein for gene GI:%s not found ...' % str(gi)
                #print locus
                
                    
            #print 'I get here'
            line = f_in.readline()
            
            #Counter
            num_done += 1
            if ((100 * num_done) / num_tot) > next_progress:
                sys.stdout.write("\r - %d %%" % next_progress)
                sys.stdout.flush()
                next_progress += 1
        
        f_in.close()
        
        #Finish counter
        sys.stdout.write("\r - 100 %\n")
        sys.stdout.flush()
