#!/usr/bin/env python
# -*- coding: utf-8 -*-
__name    = ".ctd to .html"
__version = "0.9.0"
__date    = "09.08.2013"
__author  = "Bystroushaak"
__email   = "bystrousak@kitakitsune.org"
# 
# Interpreter version: python 2.7
# This work is licensed under a Creative Commons 3.0 
# Unported License (http://creativecommons.org/licenses/by/3.0/).
# Created in Sublime text 2 editor.
#
# Notes:
	# Podporu pro <ul><li>
	# Obrázky.
#= Imports =====================================================================
import os
import sys
import urllib
import os.path
import argparse
from string import Template


from richtextools import *



#= Variables ===================================================================
OUT_DIR = "output"
TAB_SIZE = 4

HTML_TEMPLATE = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<HTML>
<head>
	<title>$title</title>
	
	<link rel="stylesheet" type="text/css" href="$rootpath/style.css">
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
</head>

<body>

$content

$copyright

</body>
</HTML>"""
COPYRIGHT = """
<!-- 
	Written in CherryTree, converted to HTML by cherrytree2html.py

	- http://www.giuspen.com/cherrytree/
	- https://github.com/Bystroushaak/cherrytree2html.py
-->
"""



#= Functions & objects =========================================================
# well, this will work everywhere and exactly how i want, not like print / print()
def write(s, out=sys.stdout):
	out.write(str(s))
	out.flush()
def writeln(s, out=sys.stdout):
	write(str(s) + "\n", out)


def printVersion():
	writeln(__name + " v" + __version + " (" + __date + ") by " + __author + " (" + __email + ")")


def listNodes(dom):
	"Return list of nodes and their IDs."

	ids   = []
	nodes = ""
	for node in dom.find("node"):
		nodes += node.params["unique_id"].ljust(4) + "- " + node.params["name"] + "\n"
		ids.append(int(node.params["unique_id"]))

	return ids, nodes


def saveNode(dom, nodeid, name = None):
	"Convert node to the HTML and save it to the HTML."

	nodeid   = str(nodeid)
	filename = getNodePath(dom, nodeid)
	rootpath = filename.count("/") * "../"
	rootpath = rootpath[:-1] if rootpath.endswith("/") else rootpath

	# ugly, bud increase parsing speed a bit
	if name == None:
		name = dom.find("node", {"unique_id" : nodeid})[0]
		name = name.params["name"]

	# generate filename, convert html
	data = convertToHtml(dom, nodeid)

	# apply html template
	data = Template(HTML_TEMPLATE).substitute(
		content   = data,
		title     = name,
		copyright = COPYRIGHT,
		rootpath  = rootpath
	)

	# check if directory tree exists - if not, create it
	directory = OUT_DIR + "/" + os.path.dirname(filename)
	if not os.path.exists(directory):
		os.makedirs(directory)

	fh = open(OUT_DIR + "/" + filename, "wt")
	fh.write(data)
	fh.close()

	return filename


def rawXml(dom, node_id):
	"Just return node XML source."

	# get node element
	node = dom.find("node", {"unique_id" : str(node_id)})[0]

	# remove subnodes
	for n in node.find("node"):
		if n.params["unique_id"] != str(node_id):
			n.replaceWith(d.HTMLElement(""))

	return str(node)



#= Main program ================================================================
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"filename",
		metavar = "FN",
		action  = "store",
		default = "",
		type    = str,
		nargs   = "?",
		help    = "Filename."
	)
	parser.add_argument(
		"-v",
		"--version",
		action  = "store_true",
		default = False,
		help    = "Print version."
	)
	parser.add_argument(
		"-l",
		"--list",
		action  = "store_true",
		default = False,
		help    = "List names of all nodes."
	)
	parser.add_argument(
		"-i",
		"--interactive",
		action  = "store_true",
		default = False,
		help    = "Interactive mode - select node and convert it to HTML."
	)
	parser.add_argument(
		"-s",
		"--save",
		action  = "store_true",
		default = False,
		help    = "Save to file named [nodeid]_[ascii_nodename].html."
	)
	parser.add_argument(
		"-a",
		"--all",
		action  = "store_true",
		default = False,
		help    = "Save all nodes to HTML."
	)
	parser.add_argument(
		"-n",
		"--node",
		metavar = "NODE ID",
		action  = "store",
		type    = int,
		default = -1,
		help    = "Print converted node to stdout."
	)
	parser.add_argument(
		"-r",
		"--raw",
		action  = "store_true",
		default = False,
		help    = "Print raw node source code (XML)."
	)
	parser.add_argument(
		"-t",
		"--template",
		metavar = "template.html",
		action  = "store",
		type    = str,
		default = None,
		help    = "Use own template. Keywords: $title, $content, $copyright, $rootpath."
	)
	args = parser.parse_args()

	if args.version:
		printVersion()
		sys.exit(0)

	if args.save and not os.path.exists(OUT_DIR):
		os.makedirs(OUT_DIR)

	if args.filename == "":
		writeln("You have to specify cherrytree xml file!", sys.stderr)
		sys.exit(1)

	# try open and read data from given location
	if os.path.exists(args.filename):
		fh = open(args.filename)
		data = fh.read()
		fh.close()
	else:
		try:
			data = urllib.urlopen(args.location).read()
		except IOError:
			writeln("Can't read '" + args.location + "'!", sys.stderr)
			sys.exit(2)

	# try read template
	if args.template != None:
		try:
			f = open(args.template)
			HTML_TEMPLATE = f.read()
			f.close()
		except IOError:
			writeln("Can't read template '" + args.template + "'!", sys.stderr)
			sys.exit(2)

	# read cherrytree file and parse it to the DOM
	dom = d.parseString(data)

	# raw - patch convertToHtml
	if args.raw:
		convertToHtml = rawXml

	# show content of cherrytree file
	if args.list:
		writeln(listNodes(dom)[1])
		sys.exit(0)
	# interactive mode
	elif args.interactive:
		ids, nodes = listNodes(dom)

		writeln(nodes, sys.stderr)
		writeln("Select node:\n", sys.stderr)

		# read userdata.
		selected = False
		while selected != True:
			write(":> ", sys.stderr)
			nodeid = raw_input("")

			# try read number from user
			try:
				nodeid = int(nodeid)
				selected = True
			except ValueError:
				writeln("\nWrong node.\n", sys.stderr)
				continue

			# check if given number can be used as ID
			if nodeid not in ids:
				writeln("\nWrong node, pick different one.\n", sys.stderr)
				selected = False
				continue

		if args.save:
			nodename = saveNode(dom, nodeid)

			writeln("\nSaved to '" + nodename + "'")
		else:
			writeln(convertToHtml(dom, str(nodeid)))

	elif args.all:
		if not os.path.exists(OUT_DIR):
			os.makedirs(OUT_DIR)

		for n in dom.find("node"):
			nodename = saveNode(dom, n.params["unique_id"].strip(), n.params["name"])
			writeln("Node '" + nodename + "' saved.")

		sys.exit(0)

	# convert selected node identified by nodeid in args.node
	elif args.node != -1:
		ids = listNodes(dom)[0]

		if args.node not in ids:
			writeln("Selected ID '" + str(args.node) + "' doesn't exists!", sys.stderr)
			sys.exit(3)

		if args.save:
			nodename = saveNode(dom, args.node)

			writeln("Saved to '" + nodename + "'")
		else:
			writeln(convertToHtml(dom, args.node))
			writeln(COPYRIGHT)
