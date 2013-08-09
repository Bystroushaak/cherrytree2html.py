#!/usr/bin/env python
# -*- coding: utf-8 -*-
__version = "1.0.0"
__date    = "09.08.2013"
__author  = "Bystroushaak"
__email   = "bystrousak@kitakitsune.org"
# 
# Interpreter version: python 2.7
# This work is licensed under a Creative Commons 3.0 
# Unported License (http://creativecommons.org/licenses/by/3.0/).
# Created in Sublime text 2 editor.
#
#= Imports =====================================================================
import unicodedata
from string import maketrans


import parser as d



#= Functions & objects =========================================================
def __utfToFilename(nodename):
	"Convert UTF nodename to ASCII."

	intab   = """ ?,@#$%^&*{}[]'"><°~\\|	"""
	outtab  = """_!!!!!!!!!!!!!!!!!!!!!!!"""
	trantab = maketrans(intab, outtab)

	nodename = nodename.decode("utf-8")
	s = unicodedata.normalize('NFKD', nodename).encode('ascii', 'ignore')

	return s.translate(trantab).replace("!", "")



def getNodePath(dom, nodeid):
	"Retun file path of node with given |nodeid|."

	# check if dom is already double-linked list
	if not hasattr(dom.childs[0], 'parent') or dom.childs[0].parent != dom:
		d.makeDoubleLinked(dom)

	# get reference to node
	node = dom.find("node", {"unique_id" : str(nodeid)})[0]

	# does this node contain another nodes?
	endpoint = len(node.find("node")) <= 1

	# get path (based on node path in dom)
	path = ""
	while node.parent != None and node.getTagName().lower() == "node":
		path = node.params["name"] + "/" + path
		node = node.parent

	if endpoint:
		path = path[:-1] # remove '/' from end of the path
	else:
		path += "index"  # index file for directory
	path += ".html"

	return __utfToFilename(path)



#= Main program ================================================================
if __name__ == '__main__':
	pass