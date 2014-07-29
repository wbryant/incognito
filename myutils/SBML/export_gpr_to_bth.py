'''
Created on 27 Mar 2014

@author: wbryant
'''

from libsbml import SBMLReader, writeSBMLToFile
import re




if __name__ == '__main__':
    
    gpr_file = '/Users/wbryant/Dropbox/UG Project - COGzymes/model data/iAH991_reactions_revised.csv'
    f_in = open(gpr_file,'r')
    gpr_dict = {}
    for line in f_in:
        cols = line.split("\t")
        gpr_dict[cols[1]] = cols[4]
    
    infile = '/Users/wbryant/Dropbox/UG Project - COGzymes/model data/BTH_iah991.xml'
    reader = SBMLReader()
    document = reader.readSBMLFromFile(infile)
    model = document.getModel()
    
    notes_string = '  <body xmlns="http://www.w3.org/1999/xhtml">\n    <p>GENE_ASSOCIATION: %s</p>\n  </body>'
    
    for reaction in model.getListOfReactions():
        
        id_rxn = reaction.getId()
        
        id_rxn = re.sub("^R_","",id_rxn)
        id_rxn = re.sub("_LPAREN_","(",id_rxn)
        id_rxn = re.sub("_RPAREN_",")",id_rxn)
        id_rxn = re.sub("_DASH_","-",id_rxn)        
        
        if id_rxn in gpr_dict:
            gpr = gpr_dict[id_rxn]
        else:
            print('%s not found ...' % id_rxn)
            gpr = ''
        
        gpr_string = notes_string % gpr
        
        reaction.setNotes(gpr_string)
    
    document.setModel(model)
    writeSBMLToFile(document,'BTH_with_gprs.xml')