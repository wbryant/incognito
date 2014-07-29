# Do import in import_SBML

import sys
sys.path.append('/Users/wbryant/work/scripts/python')
sys.path.append('/Users/wbryant/work/scripts/python/SBML')
sys.path.append('/usr/local/lib/python2.7/site-packages')

from import_SBML import *

[model, q, reaction] = import_SBML_to_bipartite('/Users/wbryant/work/MSM/network_analysis/MSM_v2.xml')

reactant = model.getReaction(1).getReactant(1)

# reactant = reaction.getReactant(1)
# id = reactant.getId
# print id