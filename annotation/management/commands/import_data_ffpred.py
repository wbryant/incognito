from django.core.management.base import NoArgsCommand, CommandError
from annotation.models import GO, Catalyst_go, Enzyme, Gene, FFPred_result
#from ffpred.extract_results import *
import sys, os, re, shelve

class FFP_prediction:
    def __init__(self, fasta = None, gi = None, go_predictions = None, job_name = None, gi_name = None):
        self.fasta = fasta or 'unknown'
        self.gi = gi or 'unknown'
        self.go_predictions = go_predictions or []
        self.job_name = job_name or 'unknown'
        self.gi_name = gi_name or 'unknown'
    
    def add_go_prediction(self, go_prediction):
        self.go_predictions.append(go_prediction)

class GO_prediction:
    def __init__(self, score, term, reliability, domain, description):
        self.score = score
        self.term = term
        self.reliability = reliability
        self.domain = domain
        self.description = description

class Command(NoArgsCommand):
    
    help = 'Imports data from FFPred runs.'
        
    def handle(self, **options):
        
        ## Extract results from data folders
        
        ffp_predictions = []
        indir = '/Users/wbryant/work/BTH/data/ffpred/output'
        
        #Find all farm jobs in input directory
        job_names = os.walk(indir).next()[1]
        
        
        for job_name in job_names:
            
            #For each job, look at all subdirectories, which each represent a single protein, and extract details for those proteins
            #for job_name in job_names:
            #job_name = job_names[0]
            job_dir = indir + '/' + job_name
            protein_names = os.walk(job_dir).next()[1]
            
            for pname in protein_names:
    
            
                #For each directory in job (each protein in job)
                #pname = protein_names[0]
                pdir = job_dir + '/' + pname
                os.chdir(pdir)
                
                #Open results file
                result_file = re.sub('FFPred_','',pname) + '.lax_formatted'
                try:
                    f_in = open(result_file, 'r')
                except:
                    print '%s not found in directory %s' % (result_file, pdir)
                
                #Find fasta name for protein and GI number, for identification
                for line in f_in:
                    line = line.strip()
                    fasta_ref = re.search('^Results for \"(gi\|([0-9]+)\|[^"]+)\"',line)
                    if fasta_ref is not None:
                        #Title line found, create prediction instantiation
                        
                        fasta = fasta_ref.group(1)
                        gi = fasta_ref.group(2)            
                        ffp_prediction = FFP_prediction(
                            fasta = fasta,
                            gi = gi,
                            job_name = job_name,
                            gi_name = pname
                        )
                        break
                
                #Now run through the rest of the file and find results lines to put into the prediction class
                for line in f_in:
                    #print line
                    line = line.strip()
                    line = line.split()
                    #print line
                    try:
                        score = float(line[0])
                    except:
                        score = -1
                    #print score
                    if score > 0: 
                        if line[3] =='MF':
                        #This is a prediction with a molecular function
                            term = line[1]
                            reliability = line[2]
                            domain = line[3]
                            
                            #Put all of the rest of the words together for the desription
                            description = ''
                            for word in line[4:]:
                                description += word
                                description += ' '
                            description = description[0:-1]
                            #print description
                            go_prediction = GO_prediction(
                                score = score,
                                term = term,
                                reliability = reliability,
                                domain = domain,
                                description = description
                            )
                            
                            ffp_prediction.add_go_prediction(go_prediction)
                ffp_predictions.append(ffp_prediction)

        
        ## Begin import into database
        
        FFPred_result.objects.all().delete()
        
        ## Import individual result
        #
        #results_file = '/Users/wbryant/work/BTH/data/ffpred/outputpredictions/predictions.dat'
        #
        #d = shelve.open(results_file)
        #
        #if 'ffp_predictions' in d:
        #    predictions = d['ffp_predictions']
        #else:
        #    print 'Predictions structure not found.'
        #    sys.exit()
        
        print 'Populating FFPred_result table ...'
        #Initiate counter
        num_tot = len(ffp_predictions)
        num_done = 0
        next_progress = 1
        sys.stdout.write("\r - %d %%" % num_done)
        sys.stdout.flush()
        
        #! Iterate here
        for prediction in ffp_predictions:
        
            gi = prediction.gi
            #print gi
            
            #! Iterate here
            for go_pred in prediction.go_predictions:
                
                score = go_pred.score
                go_term = go_pred.term
                reliability = go_pred.reliability
                
                ## Is GO term in database?  If not then discard prediction, otherwise add
                if GO.objects.filter(id=go_term).count() > 0:
                    go = GO.objects.get(id=go_term)
                    
                    
                    ## Find gene
                    if Gene.objects.filter(protein_gi=gi).count() > 0:
                        gene = Gene.objects.get(protein_gi=gi)
                        
                        # Save prediction
                        result = FFPred_result(
                            gene=gene,
                            go_term=go,
                            score=score,
                            reliability=reliability
                        )
                        
                        result.save()
                        
                        
                    #else:
                    #    print 'Gene not found: %s' % gi
                #else:
                #    print 'GO term not found: %s' % go_term
                
            #Counter
            num_done += 1
            if ((100 * num_done) / num_tot) > next_progress:
                sys.stdout.write("\r - %d %%" % next_progress)
                sys.stdout.flush()
                next_progress += 1
                
        #Finish counter
        sys.stdout.write("\r - 100 %\n")
        sys.stdout.flush()
                
                
                