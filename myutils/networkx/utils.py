'''
Created on 2 Jul 2014

@author: wbryant
'''

def nodes(G, type = None):
    """Iterator for nodes in a NetworkX graph.
    
    If 'type' is specified, filter nodes by the type specified.
    """
    
    for idx in G.nodes():
        if type:
            if G.node[idx]['type'] == type:
                yield G.node[idx], idx
        else:
            yield G.node[idx], idx

