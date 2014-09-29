'''
Created on 26 Sep 2014

@author: wbryant
'''

import math, scipy.stats

def get_z_score(a1, b1, a2, b2, one_tail = True):
    
    
    
    n1 = float(a1 + b1)
    n2 = float(a2 + b2)
    p1 = a1 / n1
    p2 = a2 / n2
    
    
    p = (a1 + a2)/float(n1 + n2)

    SE = math.sqrt( p * ( 1 - p ) * ( (1/n1) + (1/n2) ) )

    
    z = (p1 - p2) / SE
    
    if one_tail:
        p_value = scipy.stats.norm.sf(z)
    else:
        p_value = scipy.stats.norm.sf(z)*2

    return z, p_value
    

if __name__ == '__main__':
    pass