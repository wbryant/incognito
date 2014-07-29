import os, shelve, sys

if __name__ == '__main__':
    input_file = "/Users/wbryant/work/BTH/data/sequence/bth_all_proteins.fasta"
    output_folder = "/Users/wbryant/work/BTH/data/sequence/separate/"
    
    protein_number = 0
    
    f_in = open(input_file, "r")
    f_out = open(output_folder + "tmp_file.txt", "w")
    
    for line in f_in:
        if line[0] == ">":
            f_out.close()
            protein_number += 1
            file_out = output_folder + "protein_" + str(protein_number) + ".fasta"
            f_out = open(file_out, "w")
            f_out.write(line)
        else:
            f_out.write(line)
    
    f_in.close()
    f_out.close()
    
    os.remove(output_folder + "tmp_file.txt")