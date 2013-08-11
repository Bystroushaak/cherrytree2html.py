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
import sys


import parser as d
from parser import writeln
from getnodepath import *
from guessparagraphs import *



#= Variables ===================================================================
# do not wrap theese with <p>
DONT_WRAP = [
	"h1",
	"h2",
	"h3",
	"pre",
	"center",
	"table"
]



#= Functions & objects =========================================================
def __transformLink(tag, dom, node_id):
	"""
	Transform <rich_text link="webs http://kitakitsune.org">odkaz</rich_text>
	to <a href="http://kitakitsune.org">odkaz</a>.

	Also some basic link handling, ala local links and links to other nodes.
	"""

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
				depth = len(getNodePath(dom, node_id).split("/")) - 1 # get (this) node depth
				link = "./" + (depth * "../") + getNodePath(dom, link_id)

		el.params["href"] = link.strip()

		el.endtag = d.HTMLElement("</a>")
		tag.replaceWith(el)


def __transformRichText(tag):
	"Transform tag ala <rich_text some='crap'> to real html tags."

	# skip richtext nodes with no parameters (they are removed later)
	if len(tag.params) == 0:
		return

	# tags which contains nothing printable are converted just to its content
	# (whitespaces) "<h3> </h3>" -> " "
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
	def processTable(table):
		"Convert cherrytree table to HTML table."

		del table.params["char_offset"]

		html_table = str(table)
		
		html_table = html_table.replace("<cell>", "<td>")
		html_table = html_table.replace("</cell>", "</td>")
		html_table = html_table.replace("<row>", "<tr>")
		html_table = html_table.replace("</row>", "</tr>\n")
		
		return d.parseString(html_table)

	# create html versions of replacements_tagnames| tags and put them into 
	# |replacements[]| variable
	# remove |replacements_tagnames| from DOM
	replacements = []
	replacements_tagnames = ["codebox", "table"]
	for replacement in node.find("", fn = lambda x: x.getTagName() in replacements_tagnames):
		el = None

		if replacement.getTagName() == "codebox":
			el = d.HTMLElement("<pre>")
			el.childs = replacement.childs[:]
			el.params["syntax"] = replacement.params["syntax_highlighting"]
			el.endtag = d.HTMLElement("</pre>")
		elif replacement.getTagName() == "table":
			el = processTable(replacement)
		else:
			raise ValueError("This shouldn't happend. If does, HTML parser is broken.")

		replacements.append(el)

		# remove original element (codebox/table) from DOM
		replacement.replaceWith(d.HTMLElement(""))

	# replace <rich_text justification="left"></rich_text> with tags from 
	# |replacements|
	cnt = 0
	for j in node.find("rich_text", {"justification":"left"}):
		j.replaceWith(replacements[cnt])
		cnt += 1
	#===========================================================================


	# transform all <rich_text> tags to something usefull
	for t in node.find("rich_text"):
		# transform <rich_text some="crap"> to html tags
		__transformRichText(t)

		# transform links
		__transformLink(t, dom, node_id)

		# there are _arrays_ of rich_text with no params - this is not same as <p>, because <p> allows
		# nested parameters -> <p>Xex <b>bold</b></p>, but cherry tree does shit like
		# <rich_text>Xex </rich_text><rich_text weight="heavy">bold</rich_text><rich_text></rich_text>
		if len(t.params) == 0:
			el = d.HTMLElement()
			el.childs = t.childs
			t.replaceWith(el)


	# convert text to paragraphs
	node = str(node).replace('<rich_text justification="left">', "") # dont ask
	node = d.parseString(guessParagraphs(node, DONT_WRAP))

	# TODO transform • to ul/li tags

	return str(node.find("node")[0].getContent())



#= Main program ================================================================
if __name__ == '__main__':
	pass