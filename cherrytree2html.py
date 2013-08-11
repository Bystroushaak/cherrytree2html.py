#!/usr/bin/env python
# -*- coding: utf-8 -*-
__name    = ".ctd to .html"
__version = "0.10.1"
__date    = "11.08.2013"
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
	# Nějakou ukázkovou .ctd
	# TODO: sortování rss podle data
	# TODO: CSS a HTML template do nody?
#= Imports =====================================================================
import os
import sys
import urllib
import hashlib
import os.path
import argparse
from string import Template


from richtextools import *



#= Variables ===================================================================
OUT_DIR = "output"
TAB_SIZE = 4
HTML_ENTITIES = {"&lt;":"<", "&gt;":">", "&quot;":"\""}
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
ATOM_ENTRY_TEMPLATE = """
	<entry>
		<title>$title</title>
		<link href="$url"/>
		<id>http://$uid/</id>
		<updated>$updated</updated>
		<content type="html">$content</content>
	</entry>
"""
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



def generateAtomFeed(dom):
	# find RSS nodes (case insensitive)
	rss_node = dom.find(
		"",
		fn = lambda x: 
			x.getTagName() == "node" and
			"name" in x.params and 
			x.params["name"].lower() == "rss"
	)

	# don't continue, if there is no rss node
	if len(rss_node) <= 0:
		return None
	rss_node = rss_node[0]


	# iterate thru feed records
	first = True
	entries = ""
	update_times = []
	for node in rss_node.find("node"):
		# skip first iteration (main node containing information about feed)
		if first:
			first = False
			continue

		# convert node from rich_text to html
		html_node = d.parseString(convertToHtml(dom, node.params["unique_id"]))

		if len(html_node.find("a")) > 0:
			first_link = html_node.find("a")[0]
		else:
			raise ValueError("Item '" + node.params["name"] + "' doesn't have date and/or URL!")

		updated = first_link.getContent()

		# get url from first link, or set it to default
		url  = first_link.params["href"] if "href" in first_link.params else ""
		url  = "./" + url[5:] if url.startswith("./../") and len(url) > 5 else url

		# remove first link (and it's content) from html code
		if first_link != None:
			first_link.replaceWith(d.HTMLElement(""))

		# preprocess content
		content = html_node.getContent().replace("<p></p>", "").strip()
		for key, val in HTML_ENTITIES.iteritems():
			content = content.replace(val, key)


		entries += Template(ATOM_ENTRY_TEMPLATE).substitute(
			title = node.params["name"],
			url   = url,
			uid   = hashlib.md5(
				node.params["name"] +
				str(url) +
				str(updated)
			).hexdigest(),
			updated = updated,
			content = content
		)

		update_times.append(updated)

		# remove node from DOM
		node.replaceWith(d.HTMLElement(""))


	# extract Atom template from .ctd
	atom_template = rss_node.find("codebox")
	if len(atom_template) <= 0:
		raise ValueError("There is no codebox with Atom template!")
	atom_template = atom_template[0].getContent()

	for key, val in HTML_ENTITIES.iteritems():
		atom_template = atom_template.replace(key, val)


	atom_feed = Template(atom_template).substitute(
		updated = update_times[0],
		entries = entries
	)

	# get feed's filename - it is specified in atom template
	filename = d.parseString(atom_feed).find("link")
	if len(filename) <= 0:
		raise ValueError("There has to be link in your Atom template!")
	filename = filename[0]

	if not "href" in filename.params:
		raise ValueError("Link in you Atom template has to have 'href' parameter!")
	filename = filename.params["href"].split("/")[-1]

	if "." not in filename:
		filename = "atom.xml"
		writeln("There isn't specified filename of your feed, so I chosed default 'atom.xml'.")


	fh = open(OUT_DIR + "/" + filename, "wt")
	fh.write(atom_feed)
	fh.close()


	# get rid of RSS node
	rss_node.replaceWith(d.HTMLElement(""))


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
		"-d",
		"--disable-atom",
		action  = "store_true",
		default = False,
		help    = "Disable support for Atom feeds."
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

		if not args.disable_atom:
			generateAtomFeed(dom)

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
