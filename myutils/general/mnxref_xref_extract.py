#Take the data from reac_xref.tsv and convert into mapping between MetaCyc and SEED and BiGG

import sys, os, re, shelve

class Rxn_ids:
    def __init__(self, seed = None, bigg = None, metacyc = None):
        self.seed = seed or ''
        self.bigg = bigg or ''
        self.metacyc = metacyc or ''
        

if __name__ == "__main__":
    
    infile = '/Users/wbryant/work/BTH/data/mnxref/reac_xref.tsv'
    
    f_in = open(infile, 'r')
    
    reaction_dict = {}
    for line in f_in:
        if line[0] != '#':
            
            line = line.strip()
            line = line.split('\t')
            
            if line[0] == 'seed:rxn00001':
                print line
            
            mnx_id = line[1]
            if mnx_id not in reaction_dict:
                reaction_dict[mnx_id] = Rxn_ids()
            
            source_details = re.search('^([^\:]+)\:(.+)',line[0])
            source = source_details.group(1)
            id = source_details.group(2)
            if line[0] == 'seed:rxn00001':
                print source
                print id
            if source == 'bigg':
                reaction_dict[mnx_id].bigg += (id + ',')
            elif source == 'seed':
                reaction_dict[mnx_id].seed += (id + ',')
                if line[0] == 'seed:rxn00001':
                    print mnx_id
                    print source
                    print id
            elif source == 'metacyc':
                reaction_dict[mnx_id].metacyc += (id + ',')
    
    outfile = '/Users/wbryant/work/BTH/data/mnxref/reac_xref_tabulated.csv'
    
    print reaction_dict['MNXR4373'].seed
    
    f_out = open(outfile, 'w')
    f_out.write('MNX ID\tSEED ID\tBiGG ID\tMetaCyc ID\n')
    
    for reaction in reaction_dict:
        
        rxn = reaction_dict[reaction]
        
        if rxn.seed == 'rxn00001':
            print reaction
            print rxn.seed
            print rxn.bigg
            print rxn.metacyc
        
        
        
        #Is there more than one of these three DBs containing this reaction?
        num_dbs = 0
        if rxn.seed is not '':
            num_dbs += 1
            rxn.seed = rxn.seed[0:-1]
        else:
            rxn.seed = None
        if rxn.bigg is not '':
            num_dbs += 1
            rxn.bigg = rxn.bigg[0:-1]
        else:
            rxn.bigg = None
        if rxn.metacyc is not '':
            num_dbs += 1
            rxn.metacyc = rxn.metacyc[0:-1]
        else:
            rxn.metacyc = None
        
        if num_dbs > 0:
            #mnx_id = re.search('([0-9]+)',reaction).group(1)
            mnx_id = reaction
            f_out.write('%s\t%s\t%s\t%s\n' % (mnx_id, rxn.seed, rxn.bigg, rxn.metacyc))
    
    f_out.close()