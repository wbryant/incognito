from django.core.management.base import NoArgsCommand, CommandError
from annotation.models import EC, GO
import sys, re, os
from goatools import obo_parser

class Command(NoArgsCommand):
    
    help = 'Imports data to the EC table from the ORENZA website, and GO relationships .'
        
    def handle(self, **options):
        ## There are already imports from MNXRef, but this adds any that might be misasing and adds names.
        #
        #
        #print 'Removing previous ECs from this source ...\n'
        #EC.objects.filter(source='Orenza').delete()
        #
        #filename = '/Users/wbryant/work/BTH/data/ORENZA_ECs/EC_numbers.csv'
        #
        #f_in = open(filename, 'r')
        #
        #num_lines = 0
        #for line in f_in:
        #    num_lines += 1
        #f_in.close()
        #f_in = open(filename, 'r')
        #
        #print 'Populating EC table ...'
        ##Initiate counter
        #num_tot = num_lines
        #num_done = 0
        #next_progress = 1
        #sys.stdout.write("\r - %d %%" % num_done)
        #sys.stdout.flush()
        #
        #source = 'Orenza'
        #
        #for line in f_in:
        #    line = line.strip().split('\t')
        #    valid_line = False
        #    if line[0][0] != '#':
        #        valid_line = True
        #   
        #    if valid_line:
        #        number = line[0][3:]
        #        name = line[1]
        #        
        #        try:
        #            ec = EC.objects.get(number=number)
        #            ec.name = name
        #            ec.save()
        #        except:
        #            ec = EC(
        #                number = number,
        #                name = name,
        #                source = source
        #            )
        #            try:
        #                ec.save()
        #            except:
        #                print 'EC number not saved successfully: %s' % number
        #            
        #    
        #    #Counter
        #    num_done += 1
        #    if ((100 * num_done) / num_tot) > next_progress:
        #        sys.stdout.write("\r - %d %%" % next_progress)
        #        sys.stdout.flush()
        #        next_progress += 1
        #
        #f_in.close()
        #
        ##Finish counter
        #sys.stdout.write("\r - 100 %\n")
        #sys.stdout.flush()
        
        
        
        ### Import EC2GO data
        #
        #EC.objects.filter(source='geneontology').delete()
        #
        #filename = '/Users/wbryant/work/BTH/data/geneontology/ec2go.txt'
        #
        #f_in = open(filename, 'r')
        #
        #num_lines = 0
        #for line in f_in:
        #    num_lines += 1
        #f_in.close()
        #f_in = open(filename, 'r')
        #
        #print 'Populating EC2GO relationship ...'
        ##Initiate counter
        #num_tot = num_lines
        #num_done = 0
        #next_progress = 1
        #sys.stdout.write("\r - %d %%" % num_done)
        #sys.stdout.flush()
        #
        #source = 'geneontology'
        #
        #for line in f_in:
        #    
        #    line = line.strip()
        #    valid_line = False
        #    if line[0] != '#':
        #        valid_line = True
        #        valid_ids = False
        #    if valid_line:
        #        
        #        search = re.search('EC:(?P<ec_number>[^\s]+)[^;]*(?P<go_name>GO:.+)\s*;\s*(?P<go_term>GO:.+)',line)
        #        
        #        try:
        #            ec_number = search.group('ec_number')
        #            go_term = search.group('go_term')
        #            go_name = search.group('go_name')
        #            valid_ids = True
        #        except:
        #            pass
        #        
        #        if valid_ids == True:
        #            try:
        #                ec = EC.objects.get(number=ec_number)
        #            except:
        #                ec = EC(
        #                    number = ec_number,
        #                    source = source
        #                )
        #                try:
        #                    ec.save()
        #                except:
        #                    print 'EC number not saved successfully: %s' % ec_number
        #               
        #            try:
        #                go = GO.objects.get(id=go_term)
        #            except:
        #                go = GO(
        #                    id = go_term,
        #                    name = go_name
        #                )
        #                try:
        #                    go.save()
        #                except:
        #                    print 'GO term not saved successfully: %s' % go_term
        #            
        #            ec.go.add(go)
        #            ec.save()
        #                
        #    
        #    #Counter
        #    num_done += 1
        #    if ((100 * num_done) / num_tot) > next_progress:
        #        sys.stdout.write("\r - %d %%" % next_progress)
        #        sys.stdout.flush()
        #        next_progress += 1
        #
        #f_in.close()
        #
        ##Finish counter
        #sys.stdout.write("\r - 100 %\n")
        #sys.stdout.flush()
        
        
        
        ## GO ontology is then checked to see whether there are any child terms of those already mapped to EC numbers that could also be mapped to those EC numbers.
        
        # Import GO ontology
        
        print 'Importing GO Ontology ...'
        p = obo_parser.GODag('/Users/wbryant/work/BTH/data/geneontology/gene_ontology.1_2.obo')
        
        # Run through all GO terms in ec_go table
        
        terms_ec = GO.objects.filter(ec__isnull=False).distinct().values_list('id','ec__number')
        print len(terms_ec)
        
        for term in terms_ec[0:20]:
            descendants = find_nec_descendants(term[0], p, terms_ec, [])
            
            for desc in descendants:
                
                term_found = False
                try:
                    go_desc = GO.objects.get(id=desc.id)
                    term_found = True
                except:
                    print 'GO term %s not found ...' % desc.id
        
                if term_found:
                    ec
        ##! TO DO:
        
        ##! For each GO term with an EC assignment:
        ##!     - Find all child nodes without more specific EC numbers
        ##!         - assign mapping to each of those
        ##!     - Count the number of reactions for each GO term and return to a dictionary.
        

def find_nec_descendants(term, p, terms_ec, all_terms, top=True):
    """Find all descendants of a particular GO term that are not already assigned an EC number and
    assign the EC number of that term to those descendants."""
    
    #print term.id
    
    if top:
        print 'Input term: %s - %s' % (term.id, terms_ec[term.id][0])
        
    if ((term.id not in terms_ec) & (term not in all_terms)) | top:
        all_terms.append(term)
        if len(term.children) > 0:
            #print '%s has children:' % term.id
            for child in term.children:
                all_terms = find_nec_descendants(child, p, terms_ec, all_terms, False)
                #print all_terms
    elif term.id in terms_ec:
        print '%s: %s' % (term.id, terms_ec[term.id][0])
        #print ' - Cutoff term: %s - %s' % (term.id, terms_ec[term.id][0])
    
    
    return all_terms

