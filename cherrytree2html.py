#!/usr/bin/env python
# -*- coding: utf-8 -*-
__name    = ".ctd to .html"
__version = "0.7.5"
__date    = "23.05.2013"
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
import os.path
import argparse
import unicodedata
from string import maketrans
from string import Template



# well, this will work everywhere and exactly how i want, not like print / print()
def write(s, out=sys.stdout):
	out.write(str(s))
	out.flush()
def writeln(s, out=sys.stdout):
	write(str(s) + "\n", out)


try:
	import dhtmlparser as d
except ImportError:
	writeln("\nThis script require dhtmlparser.", sys.stderr)
	writeln("> https://github.com/Bystroushaak/pyDHTMLParser <\n", sys.stderr)
	sys.exit(1)



#= Variables ===================================================================
OUT_DIR = "output"
TAB_SIZE = 4
DONT_WRAP = ["h1", "h2", "h3", "pre", "center"] # do not wrap theese with <p>
HTML_TEMPLATE = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<HTML>
<head>
	<title>$title</title>
	
	<link rel="stylesheet" type="text/css" href="style.css">
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
def printVersion():
	writeln(__name + " v" + __version + " (" + __date + ") by " + __author + " (" + __email + ")")


def utfToFilename(nodename, id = 0, suffix = ".html"):
	"Convert UTF nodename to ASCII. Add id (default 0) and suffix (default .html)."

	intab   = """ ?,@#$%^&*{}[]'/"><°~\\|	"""
	outtab  = """_!!!!!!!!!!!!!!!!!!!!!!!!"""
	trantab = maketrans(intab, outtab)

	nodename = nodename.decode("utf-8")
	s = unicodedata.normalize('NFKD', nodename).encode('ascii', 'ignore')

	return str(id) + "_" + s.translate(trantab).replace("!", "") + suffix


def listNodes(dom):
	"Return list of nodes and their IDs."

	ids   = []
	nodes = ""
	for node in dom.find("node"):
		nodes += node.params["unique_id"].ljust(4) + "- " + node.params["name"] + "\n"
		ids.append(int(node.params["unique_id"]))

	return ids, nodes


def __transformLink(tag, dom):
	"""Transform <rich_text link="webs http://kitakitsune.org">odkaz</rich_text> to 
	<a href="http://kitakitsune.org">odkaz</a>.

	Also some basic link handling, ala local links and links to other nodes."""

	if "link" in tag.params:
		el = d.HTMLElement("<a>")
		el.childs = tag.childs

		# cherrytree puts string "webs "/"node " before every link for some reason
		link = tag.params["link"]
		link = link[5:]

		if tag.params["link"].startswith("webs"):
			# absolute path to local files
			if link.startswith("http:///"):
				link = link[7:]
			# relative path to local files
			if link.startswith("http://.."):
				link = link[7:]
			# relative path to local files in current directory
			if link.startswith("http://./"):
				link = link[7:]
		elif tag.params["link"].startswith("node "):
			# internal links contains only node id
			link_id = link.strip()

			# get nodename
			linked_nodename = dom.find("node", {"unique_id" : str(link_id)})
			if len(linked_nodename) == 0:
				writeln("Broken link to node ID '" + link_id + "'", sys.stderr)
				link = "[broken link to internal node]"
			else:
				linked_nodename = linked_nodename[0].params["name"]

				# convert nodename to filename - filenames contains of asciified string and nodeid
				link = "./" + utfToFilename(linked_nodename, link_id)

		el.params["href"] = link.strip()

		el.endtag = d.HTMLElement("</a>")
		tag.replaceWith(el)


def __transformRichText(tag):
	"Transform tag ala <rich_text some='crap'> to real html tags."

	# skip richtext nodes with no parameters (they are removed later)
	if len(tag.params) == 0:
		return

	# tags which contains nothing printable are converted just to its content (whitespaces) 
	# "<h3> </h3>" -> " "
	if tag.getContent().strip() == "":
		tag.params = {}
		return

	rich_text_table = [
		{"attr_key":"weight",        "attr_val":"heavy",     "tag":"strong"},
		{"attr_key":"style",         "attr_val":"italic",    "tag":"i"},
		{"attr_key":"underline",     "attr_val":"single",    "tag":"u"},
		{"attr_key":"strikethrough", "attr_val":"true",      "tag":"del"},
		{"attr_key":"family",        "attr_val":"monospace", "tag":"tt"},
		{"attr_key":"scale",         "attr_val":"h1",        "tag":"h1"},
		{"attr_key":"scale",         "attr_val":"h2",        "tag":"h2"},
		{"attr_key":"scale",         "attr_val":"h3",        "tag":"h3"},
		{"attr_key":"scale",         "attr_val":"sup",       "tag":"sup"},
		{"attr_key":"scale",         "attr_val":"sub",       "tag":"sub"},
		{"attr_key":"scale",         "attr_val":"small",     "tag":"small"},
		{"attr_key":"justification", "attr_val":"center",    "tag":"center"},
	]

	# transform tags
	for trans in rich_text_table:
		if trans["attr_key"] in tag.params and tag.params[trans["attr_key"]] == trans["attr_val"]:
			del tag.params[trans["attr_key"]]

			# put HTML tag INTO rich_text
			el = d.HTMLElement("<" + trans["tag"] + ">")
			el.childs = tag.childs
			tag.childs = [el]
			el.endtag = d.HTMLElement("</" + trans["tag"] + ">")


def guessParagraphs(s):
	def unlinkFromParent(el):
		"Unlink element from parent."

		if el.parent != None and el in el.parent.childs:
			i = el.parent.childs.index(el)
			if i >= 0:
				del el.parent.childs[i]

	def replaceInParent(el, new_el):
		"Replace element in parent.childs."

		if el.parent != None and el in el.parent.childs:
			el.parent.childs[el.parent.childs.index(el)] = new_el

	def elementToP(el):
		"""
		Convert one element to <p>el</p>. Element is changed in parent.
		Returns element (if you don't need it, just drop it, everything is changed in right place in parent already.)
		"""

		p = d.HTMLElement("<p>")

		p.childs.append(el)

		# for double linked lists
		if el.parent != None:
			p.parent  = el.parent
			replaceInParent(el, p)
			el.parent = p
		
		p.endtag = d.HTMLElement("</p>")

		return p

	def elementsToP(els):
		"""
		Put array of elements into <p>. Result is put into els.parent, so you can just call this and don't care about rest.

		Returns <p>els[:]</p>, just if you needed it.
		"""
		if len(els) == 0:
			return

		p = elementToP(els[0])

		if len(els) > 1:
			p.childs.extend(els[1:])

			for e in els[1:]:
				unlinkFromParent(e)
				e.parent = p

		return p

	def processBuffer(buff):
		"Convert array of elements in buff to paragraphs."

		p_stack = [[]]
		for el in buff:
			content = el.getContent() if el.isTag() else str(el)

			# content without \n\n is just regular part of <p>
			if not "\n\n" in content:
				p_stack[-1].append(el)
				continue

			if el.isTag():
				processBuffer(el.childs)
			else:
				# split by \n\n and convert it to tags
				tmp = map(
					lambda x: d.HTMLElement(x.strip("\n").replace("\n", "<br />\n")), # support for <br>
					content.split("\n\n")
				)

				# new tags are moved into blank container
				# original element is then replaced by this blank container
				repl = d.HTMLElement("")
				repl.childs = tmp
				el.replaceWith(repl)

				# elements must have parents
				for i in tmp:
					i.parent = el

				if len(tmp) == 0:
					p_stack.append([])
					continue

				# first element is part of previous <p>
				p_stack[-1].append(tmp[0])
				tmp = tmp[1:] if len(tmp) > 1 else [] # del tmp[0] <- this tends to delete object in tmp[0] .. wtf?

				# other elements are new <p>s by itself
				for i in tmp:
					p_stack.append([i])

		# convert stack of elements to <p>
		for p in p_stack:
			elementsToP(p)

	# parse string and make it double-linked tree
	node = d.parseString(s)
	d.makeDoubleLinked(node)

	# get all elements between <hx> (headers) - they will be converted to <p>aragraphs
	tmp = []
	buffs = []
	for el in node.childs[0].childs:
		if el.getTagName().lower() in DONT_WRAP and not el.isEndTag():
			buffs.append(tmp)
			tmp = []
		else:
			tmp.append(el)
	buffs.append(tmp)

	# process paragraphs
	for buff in buffs:
		processBuffer(buff)

	# remove blank <p>aragraphs
	map(lambda x: x.replaceWith(d.HTMLElement("")), filter(lambda x: x.getContent().strip() == "", node.find("p")))

	# return "beautified" string
	return str(node)                               \
	                .replace("<p>", "\n<p>")       \
	                .replace("</p>", "</p>\n\n")   \
	                .replace("<p>\n", "<p>")       \
	                .replace("<h", "\n<h")



def convertToHtml(dom, node_id):
	# get node element
	node = dom.find("node", {"unique_id" : str(node_id)})[0]
	node = d.parseString(str(node)).find("node")[0] # easiest way to do deep copy

	# remove subnodes
	for n in node.find("node"):
		if n.params["unique_id"] != str(node_id):
			n.replaceWith(d.HTMLElement(""))


	#===========================================================================
	# transform <codebox>es to <pre> tags.
	# CherryTree saves <codebox>es at the end of the <node>. Thats right - they 
	# are not in the source as all other tags, but at the end. Instead of 
	# <codebox> in the text, there is <rich_text justification="left"></rich_text>
	# That needs to be replaced with <pre>

	# remove <codeboxes> from DOM, create new pre tags and put them into
	# codeboxes[] variable
	codeboxes = []
	for codebox in node.find("codebox"):
		el = d.HTMLElement("<pre>")
		el.childs = codebox.childs[:]
		el.params["syntax"] = codebox.params["syntax_highlighting"]
		el.endtag = d.HTMLElement("</pre>")
		codeboxes.append(el)

		# remove original <codebox> from DOM
		codebox.replaceWith(d.HTMLElement(""))

	# replace <rich_text justification="left"></rich_text> with <pre> tags
	cnt = 0
	for j in node.find("rich_text", {"justification":"left"}):
		j.replaceWith(codeboxes[cnt])
		cnt += 1
	#===========================================================================


	# transform all <rich_text> tags to something usefull
	for t in node.find("rich_text"):
		# transform <rich_text some="crap"> to html tags
		__transformRichText(t)

		# transform links
		__transformLink(t, dom)

		# there are _arrays_ of rich_text with no params - this is not same as <p>, because <p> allows
		# nested parameters -> <p>Xex <b>bold</b></p>, but cherry tree does shit like
		# <rich_text>Xex </rich_text><rich_text weight="heavy">bold</rich_text><rich_text></rich_text>
		if len(t.params) == 0:
			el = d.HTMLElement()
			el.childs = t.childs
			t.replaceWith(el)


	# convert text to paragraphs
	node = str(node).replace('<rich_text justification="left">', "") # dont ask
	node = d.parseString(guessParagraphs(node))

	# TODO transform • to ul/li tags

	return str(node.find("node")[0].getContent()) + COPYRIGHT


def saveNode(dom, nodeid, name = None):
	"Convert node to the HTML and save it to the HTML."

	# ugly, bud increase parsing speed a bit
	if name == None:
		name = dom.find("node", {"unique_id" : str(nodeid)})[0]
		name = name.params["name"]

	# generate filename, convert html
	filename = utfToFilename(name, str(nodeid))
	data     = convertToHtml(dom, str(nodeid))

	# apply html template
	data = Template(HTML_TEMPLATE).substitute(
		content   = data,
		title     = name,
		copyright = COPYRIGHT
	)

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
	args = parser.parse_args()

	if args.version:
		printVersion()
		sys.exit(0)

	if args.filename == "":
		writeln("You have to specify cherrytree xml file!", sys.stderr)
		sys.exit(1)
	if not os.path.exists(args.filename):
		writeln("Specified filename '" + args.filename + "' doesn't exists!", sys.stderr)
		sys.exit(2)
	if args.save and not os.path.exists(OUT_DIR):
		os.makedirs(OUT_DIR)

	# read cherrytree file and parse it to the DOM
	fh = open(args.filename)
	dom = d.parseString(fh.read())
	fh.close()

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
