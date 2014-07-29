from django.core.management.base import NoArgsCommand, CommandError
from django.db.models import Count
from django.db import connection
from annotation.models import EC, GO, GO2EC, Source
import sys, re, os
from goatools import obo_parser

class Command(NoArgsCommand):
    
    help = 'Imports data to the EC table from the ORENZA website, and GO relationships .'
        
    def handle(self, **options):

        ## There are already imports from MNXRef, but this adds any that might be missing and adds names.
        
        ##! Adds reaction relationships too?!  Otherwise, what's the point?
        
        print 'Removing previous ECs from this source ...\n'
        EC.objects.filter(source__name='Orenza').delete()
        
        filename = '/Users/wbryant/work/BTH/data/ORENZA_ECs/EC_numbers.csv'
        
        f_in = open(filename, 'r')
        
        num_lines = 0
        for line in f_in:
            num_lines += 1
        f_in.close()
        f_in = open(filename, 'r')
        
        print 'Populating EC table ...'
        #Initiate counter
        num_tot = num_lines
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()

        source_id = 'Orenza'
        
        if source_id in Source.objects.all().values_list("name", flat=True):
            source = Source.objects.get(name=source_id)
        else:
            source = Source(name=source_id)
            source.save()
       
        
        
        for line in f_in:
            line = line.strip().split('\t')
            valid_line = False
            if line[0][0] != '#':
                valid_line = True
           
            if valid_line:
                number = line[0][3:]
                name = line[1]
                
                num_periods = number.count('.')
                    
                periods_needed = 3 - num_periods
                    
                for i in range(0,periods_needed):
                    number += '.-'
                
                try:
                    ec = EC.objects.get(number=number)
                    ec.name = name
                    ec.save()
                except:
                    ec = EC(
                        number = number,
                        name = name,
                        source = source
                    )
                    try:
                        ec.save()
                    except:
                        print 'EC number not saved successfully: %s' % number
                    
            
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
        
        
        
        ### Import EC2GO data
        
        EC.objects.filter(source="Gene Ontology").delete()
        GO2EC.objects.filter(source="Gene Ontology").delete()
        
        
        #cursor = connection.cursor()
        #cursor.execute("TRUNCATE TABLE annotation_ec_go;")
        
        filename = '/Users/wbryant/work/BTH/data/geneontology/ec2go.txt'
        
        f_in = open(filename, 'r')
        
        num_lines = 0
        for line in f_in:
            num_lines += 1
        f_in.close()
        f_in = open(filename, 'r')
        
        print 'Populating EC2GO relationship ...'
        #Initiate counter
        num_tot = num_lines
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()
        
        source = "Gene Ontology"
        if source_id in Source.objects.all().values_list("name", flat=True):
            source = Source.objects.get(name=source_id)
        else:
            source = Source(name=source_id)
            source.save()
        
        for line in f_in:
            
            line = line.strip()
            valid_line = False
            if line[0] != '#':
                valid_line = True
                valid_ids = False
            if valid_line:
                
                search = re.search('EC:(?P<ec_number>[^\s]+)[^;]*(?P<go_name>GO:.+)\s*;\s*(?P<go_term>GO:.+)',line)
                
                try:
                    ec_number = search.group('ec_number')
                    go_term = search.group('go_term')
                    go_name = search.group('go_name')
                    valid_ids = True
                except:
                    pass
                
                
                
                if valid_ids == True:
                    
                    # Convert EC numbers to include hyphens for unknown digits.
                
                    num_periods = ec_number.count('.')
                    
                    periods_needed = 3 - num_periods
                    
                    for i in range(0,periods_needed):
                        ec_number += '.-'
                    
                    #if periods_needed == 3:
                    #    print ec_number
                    
                    try:
                        ec = EC.objects.get(number=ec_number)
                    except:
                        ec = EC(
                            number = ec_number,
                            source = source
                        )
                        try:
                            ec.save()
                        except:
                            print 'EC number not saved successfully: %s' % ec_number
                       
                    try:
                        go = GO.objects.get(id=go_term)
                    except:
                        go = GO(
                            id = go_term,
                            name = go_name
                        )
                        try:
                            go.save()
                        except:
                            print 'GO term not saved successfully: %s' % go_term
                    
                    go2ec = GO2EC(
                        go = go,
                        ec = ec,
                        source="Gene Ontology"
                    )
                    
                    go2ec.save()
            
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
        
        
        
        ### GO ontology is then checked for propagating EC numbers to relevant GO terms.
        
        ## Import GO ontology
        
        print 'Importing GO Ontology ...'
        p = obo_parser.GODag('/Users/wbryant/work/BTH/data/geneontology/gene_ontology.1_2.obo')
        
        ## Delete old go2ec relationships
        GO2EC.objects.filter(source__contains="ancestor").delete()
        GO2EC.objects.filter(source__contains="descendant").delete()
        GO2EC.objects.filter(source__contains="Unassigned").delete()
        
        ## Create dictionary of EC numbers with GO terms as the key, and the inverse
        terms_ec = GO.objects.filter(ec__isnull=False).distinct().values_list('id','ec__number')
        go2ec_dict = {}
        for term in terms_ec:
            if term[0] not in go2ec_dict:
                go2ec_dict[term[0]] = term[1]
            else:
                ## Keep most specific term
                #print term[0]
                new_count = term[1].count('-')
                old_count = go2ec_dict[term[0]].count('-')
                if new_count < old_count:
                    go2ec_dict[term[0]] = term[1]
                    #print " => %s: %s" % (term[0], term[1])
            
            #if term[1].count('-') == 1:
            #    print "%s: %s" % (term[0], term[1])
        
        ec2go_dict = {}
        for term in go2ec_dict:
            ec2go_dict[go2ec_dict[term]] = term
            
            #if go2ec_dict[term].count('-') == 1:
            #    print '%s: %s' % (go2ec_dict[term], term)
            
            
        ## Find all 4-digit EC numbers without a corresponding GO term
        ecs_no_go = EC.objects.filter(go_terms__isnull=True, number__regex=".+\..+\..+\..+").distinct().values_list('number', flat=True)
        
        
        ## Create dictionary containing all general (3-digit) GO records, with EC number as key
        go_3_digit_dict = {}
        go_3_digit = GO.objects.filter(ec__number__regex="^[0-9]+\.[0-9]+\.[0-9]+\.-")
        for go in go_3_digit:
            #print '%s: %s' % (go.id, str(go.ec_set.get(number__regex="^[0-9]+\.[0-9]+\.[0-9]+\.-")))
            try:
                ec_number = str(go.ec_set.get(number__regex="^[0-9]+\.[0-9]+\.[0-9]+\.-", go2ec__source="Gene Ontology"))
            except:
                print "Too many ECs for %s" % go.id
                print go.ec_set.filter(number__regex="^[0-9]+\.[0-9]+\.[0-9]+\.-").values_list('number', flat=True)
                exit(1)
            go_3_digit_dict[ec_number] = go
            #print '%s: %s' % (ec_number, go.id)
        
        ## How many 4-digit ECs without GO terms are there for each 3-digit EC?
        
        ec_34_dict = {}
        
        for ec in ecs_no_go:
            ec_separated = re.search('^([^\.]+\.[^\.]+\.[^\.]+)\.(.+)', ec)
            
            ec_3_digits = ec_separated.group(1) + '.-'
            fourth_digit = ec_separated.group(2)
            
            #print ec_3_digits
            #print fourth_digit
            
            if ec_3_digits in ec_34_dict:
                ec_34_dict[ec_3_digits].append(ec)
            else:
                ec_34_dict[ec_3_digits] = [ec]
        
        ecs_3_all = EC.objects.filter(number__regex="^[0-9]+\.[0-9]+\.[0-9]+\.-").values_list('number', flat=True)
        
        print "Number of 3-digit ECs: %d" % len(ecs_3_all)
        
        ### For each 3-digit GO, assign EC numbers to all descendants
        ## for ec_3 in go_3_digit_dict:
        for ec_3 in ecs_3_all:
            
            
            if ec_3 in go_3_digit_dict:
                
                ## create set of non-EC descendants of this GO term
                go_3 = go_3_digit_dict[ec_3]    
                go_3_term = p[go_3.id]
                go_3_descs = find_nec_descendants(go_3_term, go2ec_dict)
                go_3_descs_set = set()
                for desc in go_3_descs:
                    if desc.id not in [go_3.id]:
                        go_3_descs_set.add(desc.id)
                ec_3_db = EC.objects.get(number=ec_3)
                
                print "Calculating ECs for descendants of GO with EC %s (%s)..." % (ec_3, go_3.id)
                
                ## For each 4-digit GO descended from that 3-digit GO, find ancestors to 3 generations or until 3-digit GO is found
                ##  - add 4-digit EC to all of these ancestors
                all_4_digit_ancestors = set()
                go_4_ancestors_dict = {}
                go_4_ancestors_dict[ec_3] = {}
                go_4_ancestors_dict[ec_3][ec_3] = set()
                        
                ## Create regex to get all 4-digit ECs for 3-digit GO
                ec_regex_parts = re.search('([0-9]+)\.([0-9]+)\.([0-9]+)\.-',ec_3)
                ec_regex = r'^%s\.%s\.%s\.[^-]+' % (ec_regex_parts.group(1), ec_regex_parts.group(2), ec_regex_parts.group(3))
                
                ## Retrieve all 4-digit ECs
                ecs_4_go = EC.objects.filter(go2ec__isnull=False, number__regex=ec_regex).values_list('number', flat=True)
                
                for ec_4 in ecs_4_go:
                    
                    ## Get GO term for EC
                    if ec_4 in ec2go_dict:
                        go_4_id = ec2go_dict[ec_4]
                        go_4_term = p[go_4_id]
                        
                        ## Find all GO terms up to great grandparents, or until 3-digit GO is found
                        go_4_ancestors_dict[ec_3][ec_4] = set()
                        go_4_ancestors = set()
                        go_4_parents = go_4_term.parents
                        go_4_gparents = []
                        go_4_ggparents = []
                        
                        if go_3_term not in go_4_parents:
                            for parent in go_4_parents:
                                go_4_ancestors.add(parent)
                                go_4_gparents.extend(parent.parents)
                            if go_3_term not in go_4_gparents:
                                for gparent in go_4_gparents:
                                    go_4_ancestors.add(gparent)
                                    go_4_ggparents.extend(gparent.parents)
                                if go_3_term not in go_4_ggparents:
                                    for ggparent in go_4_ggparents:
                                        go_4_ancestors.add(ggparent)
                        
                        for ancestor in go_4_ancestors:
                            go_4_ancestors_dict[ec_3][ec_3].add(ancestor.id)
                            go_4_ancestors_dict[ec_3][ec_4].add(ancestor.id)
                
                ## get all 4-digit ECs that are not linked to GO terms
                ecs_4_non_go = EC.objects.filter(go2ec__isnull=True, number__regex=ec_regex)
                
                ## for each 4-digit EC without a GO, assign it to the 3-digit GO
                for ec in ecs_4_non_go:
                    
                    go2ec = GO2EC(
                        go=go_3,
                        ec=ec,
                        source="Unassigned EC"
                    )
                    
                    go2ec.save()
                    
    
                ### Compare 4-digit ancestors to 3-digit descendants and give 
                
                found_example = False
                
                ## for each 4-digit GO, add 4-digit EC to all ancestors
                for ec_3 in go_4_ancestors_dict:
                    for ec_4 in go_4_ancestors_dict[ec_3]:
                        if ec_4 != ec_3:                    
                            
                            ## Get 4-digit EC DB entry
                            ec_4_db = EC.objects.get(number=ec_4)
                            
                            for ec_4_ancestor in go_4_ancestors_dict[ec_3][ec_4]:    
                                try:
                                    
                                    ## Get ancestor GO DB entry
                                    ancestor_go = GO.objects.get(id=ec_4_ancestor)
                                
                                    ## Add EC number to that GO term
                                    
                                    go2ec = GO2EC(
                                        go=ancestor_go,
                                        ec=ec_4_db,
                                        source="%s ancestor" % ec_4
                                    )
                                    
                                    go2ec.save()
                                    
                                    #ancestor_go.ec_set.add(ec_4_db)
                                
                                except:
                                    print " - No GO term corresponding to EC %s for ancestor %s" % (ec_4, ec_4_ancestor) 
                                
                ###!  WHAT ORDER ARE THE ASSIGNMENTS MADE??!!                
                
                ### Compare 4-digit ancestors to 3-digit descendants and give 3-digit only terms 3-digit GO list of terms
                
                ## Find 4-digit descendants of 3-digit GO that are not ancestors of any 4-digit GOs.
                go_3_descendants = go_3_descs_set
                go_4_all_ancestors = go_4_ancestors_dict[ec_3][ec_3]
                go_3_non_ec = go_3_descendants - go_4_all_ancestors
                #go_3_db = GO.objects.get(id=go_3.id)
                ecs_go_3 = go_3.ec_set.all()
                
                
                ## Add 3-digit GOs to all relevant descendant terms
                for go in go_3_non_ec:
                    go_new = GO.objects.get(id=go)
                    for ec in ecs_go_3:
                        
                        go2ec = GO2EC(
                            go=go_new,
                            ec=ec,
                            source="%s descendant" % go_3.id
                        )
                        
                        go2ec.save()
                        
                        #try:
                        #    go2ec.save()
                        #except:
                        #    print go_new.id
                        #    print " - %s descendant" % go_3.id
                        
                        #go_new.ec_set.add(ec)
                
                ### Finally, add 4-digit ECs that have GO terms to 3-digit GOs (done last so that
                ### they are not propagated to 3-digit GO descendants)
                
                ec_regex = r'^%s\.%s\.%s\.[^-]+' % (ec_regex_parts.group(1), ec_regex_parts.group(2), ec_regex_parts.group(3))
                ecs_4_go = EC.objects.filter(go2ec__isnull=False, number__regex=ec_regex)
                
                for ec_4 in ecs_4_go:
                    go2ec = GO2EC(
                        go=go_3,
                        ec=ec_4,
                        source="%s general term" % go_3.id
                    )
                    go2ec.save()
                
            else:
                print " - No GO term corresponding to EC %s\n" % ec_3

def find_nec_descendants(term, terms_ec, all_terms = None, top=True):
    """Find all descendants of a particular GO term that are not already assigned an EC number."""
    
    if not all_terms:
        all_terms = []
    
    if ((term.id not in terms_ec) & (term not in all_terms)) | top:
        #print term.id
        all_terms.append(term)
        if len(term.children) > 0:
            #print '%s has children:' % term.id
            for child in term.children:
                all_terms = find_nec_descendants(child, terms_ec, all_terms, False)
                #print all_terms
    
    return all_terms

def ec2go(term_id, dictionary = None):
    
    ## Get Gene Ontology EC2GO relationships as found in database
    
    if dictionary == None:
        try:
            go = GO2EC.objects.get(ec_id=term_id, source="Gene Ontology")
            return go.go_id
        except:
            try:
                ec = GO2EC.objects.get(go_id=term_id, source="Gene Ontology")
                return ec.ec_id
            except:
                return ''
    
    elif term_id in dictionary:
        return dictionary[term_id]
    else:
        return ''
    