#Merge directories

from numpy import *
from scipy import *
from math import *
import networkx as nx
from time import time, sleep
import operator
import sys
import re
import os
import shelve
import argparse
from libsbml import *
from copy import *
from urllib import urlretrieve
import shutil

def merge_directories(directory_src, directory_dst):
    #Merge directory2 into directory 1, adding missing files a single directory
    #deep
    
    subdirs_src = os.walk(directory_src).next()[1]
    subdirs_dst = os.walk(directory_dst).next()[1]
    
    for dir in subdirs_src:
        subdir_src = directory_src + '/' + dir
        subdir_dst = directory_dst + '/' + dir
        if dir not in subdirs_dst:
            shutil.copytree(subdir_src, directory_dst)
        else:
            files_src = os.listdir(subdir_src)
            files_dst = os.listdir(subdir_dst)
            for file_src in files_src:
                if file_src not in files_dst:
                    src = subdir_src + '/' + file_src
                    shutil.copy2(src, subdir_dst)