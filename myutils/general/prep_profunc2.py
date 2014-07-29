import sys, os, glob, time
#import subprocess, shlex

if __name__ == '__main__':
    
    folder = "/Users/wbryant/work/BTH/data/profunc/wbryant_pdbs2/"
    
    os.chdir(folder)
    
    files = glob.glob("*.pdb")
    
    list_num = 0
    
    summary_file = "dataset_003001.lst"
    
    f_out = open(summary_file, "w")
    
    for file in files:
        
        list_num += 1
        
        #print("%d - %s" % (list_num, file))
        
        run_id = 3000 + list_num
        
        if (list_num - 1) / 100 == (list_num - 1) / 100.0:
            f_out.close()
            summary_file = "dataset_%06d.lst" % run_id
            f_out = open(summary_file, "w")
        
        f_out.write("%s\n" % file)
        
    
    f_out.close()
        
        
        