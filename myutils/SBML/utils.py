'''
Created on 20 May 2014

@author: wbryant
'''

import re, sys
from myutils.general.utils import loop_counter

def file_len(fname):
    with open(fname) as f:
        for i, _ in enumerate(f):
            pass
    return i + 1

def strip_model_boundary(model_file_in, model_file_out = None, boundary_name = 'b'):
    """Remove boundary compartment from SBML model."""
    
    f_in = open(model_file_in, 'r')
    
    counter = loop_counter(file_len(model_file_in))
    
    if not model_file_out:
        model_file_out = re.sub("(\.[^\.]+)$","_no_boundary\g<1>",model_file_in) 
    
    model_file_tmp = re.sub("(\.[^\.]+)$","_no_boundary.tmp",model_file_in)
    
    f_out = open(model_file_tmp, 'w')
    line = f_in.readline()
    counter.step()
    
    compartment_regexp = '<compartment[^>]+id="([^"]+)"[^>]+name="b"[^>]+>(?:</compartment>){0,1}'
    boundary_id = None 
    
    print("Look for compartment ...")
    
    while "<listOfSpecies>" not in line:
        ## Look for compartment
        
        compartment_found = False
        
        if "compartment" in line:
            line_out = re.sub(compartment_regexp, "", line)
            if (line_out != line) and not boundary_id:
                comp_match = re.search(compartment_regexp, line)
                try:
                    boundary_id = comp_match.group(1)
                    compartment_found = True
                except:
                    print("Boundary ID could not be found ...")
                    sys.exit(1)
        else:
            line_out = line
        
        f_out.write(line_out)
        line = f_in.readline()
        counter.step()
    
    if not compartment_found:
        print("Compartment not found ...")
    
    boundary_mets = []
    met_boundary_text = '<species.+id="([^"]+)".+compartment="' + boundary_id + '".+>'
    
    print("Look for species ...")
    
    while "</listOfSpecies>" not in line:
        ## Look for all species in the boundary
        
        id_match = re.search(met_boundary_text, line)
        
        if id_match:
            boundary_mets.append(id_match.group(1))
            
            ## Search through text to </species>, leaving it all out of f_out
            
            while "</species>" not in line:
                line = f_in.readline()
                counter.step()
        else:
            f_out.write(line)
        
        line = f_in.readline()
        counter.step()
    
    reaction_text = '<reaction.+id="([^"]+)"[^>]+>'
    boundary_rxns = []
    rxn_id = ''
    species_reference_text = '<speciesReference[^>]+species="([^"]+)"[^>]+>(?:</speciesReference>){0,1}'
    
    print("Look for reactions ...")
    
    while "</listOfReactions>" not in line:
        
        ## Find all lines in reactions mentioning boundary metabolites and eliminate them. Note reaction IDs so they can be renamed with 'EX_'
        
        if "<reaction" in line:
            try:
                rxn_id = re.search(reaction_text,line).group(1)
            except:
                print("Reaction not properly formed:\n - {}".format(line))
            
        if "<speciesReference" in line:
            try:
                met_id = re.search('species="([^"]+)"',line).group(1)
                
                line_new = line
                
                if met_id in boundary_mets:
                    boundary_rxns.append(rxn_id)
                    line_new = re.sub(species_reference_text,"",line)
                
                f_out.write(line_new)
                
            except:
                print("SpeciesReference not properly formed:\n - {}".format(line))
        else:
            f_out.write(line)        
        
        line = f_in.readline()
        counter.step()
    
    counter.stop()
    f_in.close()
    f_out.close()
    
    ### Update exchange reaction names
    
    f_in = open(model_file_tmp, 'r')
    f_out = open(model_file_out, 'w')
    
    for line in f_in:
        line_out = line
        try:
            rxn_id = re.search(reaction_text, line).group(1)
            if rxn_id in boundary_rxns:
                line_out = re.sub('(id="(?:R_){0,1})([^"]+"))','\g<1>EX_\g<2>',line)
        except:
            pass
        
        f_out.write(line_out)
    
    f_in.close()
    f_out.close()
    
    

if __name__ == '__main__':
    pass