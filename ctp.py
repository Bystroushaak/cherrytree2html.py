#!/usr/bin/env python
# -*- coding: utf-8 -*-
__name    = ".ctd to .html"
__version = "0.2.1"
__date    = "07.12.2012"
__author  = "Bystroushaak"
__email   = "bystrousak@kitakitsune.org"
# 
# Interpreter version: python 2.7
# This work is licensed under a Creative Commons 3.0 
# Unported License (http://creativecommons.org/licenses/by/3.0/).
# Created in Sublime text 2 editor.
#
# Notes:
    # Obrázky.
    # Vlastní vychytávky ala strong/stroked.
    # Interaktivní režim.
#= Imports =====================================================================
import sys
import os.path
import argparse
import unicodedata
from string import maketrans


from mfn import html as d



#= Variables ===================================================================



#= Functions & objects =========================================================
def write(s, out=sys.stdout):
	out.write(str(s))
	out.flush()
def writeln(s, out=sys.stdout):
	write(str(s) + "\n")
def printVersion():
	writeln(__name + " v" + __version + " (" + __date + ") by " + __author + " (" + __email + ")")


def utfToFilename(nodename, id = 0, suffix = ".html"):
	"Convert UTF nodename to ASCII. Add id (default 0) and suffix (default .html)."

	intab   = """ ?,@#$%^&*{}[]'"><°~\\|	"""
	outtab  = """_!!!!!!!!!!!!!!!!!!!!!!!"""
	trantab = maketrans(intab, outtab)

	nodename = nodename.decode("utf-8")
	s = unicodedata.normalize('NFKD', nodename).encode('ascii', 'ignore')

	return str(id) + "_" + s.translate(trantab).replace("!", "") + suffix


def listNodes(dom):
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

	# skip blank richtext nodes
	if len(tag.params) == 0:
		return 

	rich_text_table = [
		{"attr_key":"weight",        "attr_val":"heavy",     "tag":"strong"},
		{"attr_key":"style",         "attr_val":"italic",    "tag":"i"},
		{"attr_key":"underline",     "attr_val":"single",    "tag":"u"},
		{"attr_key":"strikethrough", "attr_val":"true",      "tag":"strike"},
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

			el = d.HTMLElement("<" + trans["tag"] + ">")
			el.childs = tag.childs
			tag.childs = [el]
			el.endtag = d.HTMLElement("</" + trans["tag"] + ">")


def convertToHtml(dom, node_id):
	# get node element
	node = dom.find("node", {"unique_id" : str(node_id)})[0]

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

	# transoform <codebox>es to <pre> tags
	for t in node.find("codebox"):
		el = d.HTMLElement("<pre>")
		el.childs = t.childs
		el.params["syntax"] = t.params["syntax_highlighting"]
		el.endtag = d.HTMLElement("</pre>")
		t.replaceWith(el)

	# dont ask..
	node = d.parseString(str(node))

	# generate p
	out = ""
	tmp = ""
	for t in node.childs[0].childs:
		n = t.getTagName().lower()
		if n != "h1" and n != "h2" and n != "h3" and n != "pre":
			tmp += str(t)
			if str(t).endswith("\n\n"):
				out += "<p>" + tmp.strip().replace("\n\n", "</p>\n\n<p>") + "</p>\n\n"
				tmp = ""
		else:
			if str(t).strip() != "":
				out += str(t) + "\n\n"

	# TODO transform • to ul/li tags

	return str(out)



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
		"-l",
		"--list",
		action  = "store_true",
		default = False,
		help    = "List names of all nodes."
	)
	parser.add_argument(
		"-n",
		"--node",
		metavar = "NODE ID",
		action  = "store",
		type    = int,
		default = -1,
		help    = "Parse node ."
	)
	args = parser.parse_args()

	if args.filename == "":
		writeln("You have to specify cherrytree xml file!", sys.stderr)
		sys.exit(1)
	if not os.path.exists(args.filename):
		writeln("Specified filename '" + args.filename + "' doesn't exists!", sys.stderr)
		sys.exit(2)

	# read cherrytree file and parse it to the DOM
	fh = open(args.filename)
	dom = d.parseString(fh.read())
	fh.close()

	# show content of cherrytree file
	if args.list:
		writeln(listNodes(dom)[1])
		sys.exit(0)

	# convert selected node identified by nodeid in args.node
	if args.node != -1:
		ids = listNodes(dom)[0]

		if args.node not in ids:
			writeln("Selected ID '" + str(args.node) + "' doesn't exists!", sys.stderr)
			sys.exit(3)

		writeln(convertToHtml(dom, args.node))