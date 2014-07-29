import sys, os, glob, time
#import subprocess, shlex

if __name__ == '__main__':
    
    folder = "/Users/wbryant/work/BTH/data/profunc/wbryant_pdbs2/"
    
    os.chdir(folder)
    
    files = glob.glob("*.pdb")
    
    for file in files:
        
        f_in = open(file, "r")
        f_out = open("p" + file, "w")
        f_out.write("TITLE\tp" + file + "\n")
        
        for line in f_in:
            f_out.write(line)
        
        f_in.close()
        f_out.close()
        
        
        