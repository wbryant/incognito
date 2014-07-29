#Take the data from reac_xref.tsv and convert into mapping between MetaCyc and SEED and BiGG

import sys, os, re, shelve

class Rxn_ids:
    def __init__(self):
        self.seed = None
        self.bigg = None
        self.metacyc = None
        

if __name__ == "__main__":
    
    infile = '/Users/wbryant/work/BTH/data/mnxref/reac_prop.tsv'
    
    f_in = open(infile, 'r')
    
    reaction_dict = {}
    for line in f_in:
        line = line.strip()
        line = line.split('\t')
        #print line
        if len(line) > 5:
            #print line
            #print line[0]
            #print line[1]
            if re.search('^MNXR',line[0]):
                if line[0] not in reaction_dict:
                    reaction_dict[line[0]] = Rxn_ids()
                sources = re.search('^([^\:]+)\:(.+)',line[5])
                source = sources.group(1)
                id = sources.group(2)
                if line[0] == 'MNXR10':
                    print '%s\t%s' % (source, id)
                #print id
                if source == 'bigg':
                    reaction_dict[line[0]].bigg = id
                elif source == 'seed':
                    reaction_dict[line[0]].seed = id
                elif source == 'metacyc':
                    reaction_dict[line[0]].metacyc = id
    
    outfile = '/Users/wbryant/work/BTH/data/mnxref/reac_xref_tabulated.csv'
    
    f_out = open(outfile, 'w')
    f_out.write('MNX ID\tSEED ID\tBiGG ID\tMetaCyc ID\n')
    
    for reaction in reaction_dict:
        rxn = reaction_dict[reaction]
        
        #Is there more than one of these three DBs containing this reaction?
        num_dbs = 0
        if rxn.seed is not None:
            num_dbs += 1
        if rxn.bigg is not None:
            num_dbs += 1
        if rxn.metacyc is not None:
            num_dbs += 1
        
        if num_dbs > 1:
            mnx_id = re.search('([0-9]+)',reaction).group(1)
            f_out.write('%s\t%s\t%s\t%s\n' % (mnx_id, rxn.seed, rxn.bigg, rxn.metacyc))
    
    f_out.close()