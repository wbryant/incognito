'''
Created on 8 Aug 2014

@author: wbryant
'''

from selenium import webdriver

browser = webdriver.Firefox()
browser.get('http://localhost:8000')

assert 'Django' in browser.title