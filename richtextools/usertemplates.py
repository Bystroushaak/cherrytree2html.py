#!/usr/bin/env python
# -*- coding: utf-8 -*-
__version = "1.0.0"
__date    = "20.08.2013"
__author  = "Bystroushaak"
__email   = "bystrousak@kitakitsune.org"
# 
# Interpreter version: python 2.7
# This work is licensed under a Creative Commons 3.0 
# Unported License (http://creativecommons.org/licenses/by/3.0/).
# Created in Sublime text 2 editor.
#
#= Imports =====================================================================
import os.path
import hashlib
from string import Template


import parser as d
from parser        import writeln
from converttohtml import convertToHtml



#= Variables ===================================================================
HTML_ENTITIES = {"&lt;":"<", "&gt;":">", "&quot;":"\""}
ATOM_ENTRY_TEMPLATE = """
	<entry>
		<title>$title</title>
		<link href="$url"/>
		<id>http://$uid/</id>
		<updated>$updated</updated>
		<content type="html">$content</content>
	</entry>
"""



#= Functions & objects =========================================================
def __getFirstNodeByCIName(dom, nodename):
	"find RSS nodes (case insensitive)"
	out_node = dom.find(
		"",
		fn = lambda x: 
			x.getTagName() == "node" and
			"name" in x.params and 
			x.params["name"].lower() == nodename
	)

	if len(out_node) <= 0:
		return None
	
	return out_node[0]


def __getUserTemplate(dom, name):
	""""
	Return users template identified by name (case insensitive).

	Template is then converted to html.

	Returns: (template_node, html_content)
	"""
	template_node = __getFirstNodeByCIName(dom, name)

	# don't continue, if there is no rss node
	if template_node is None:
		return (None, None)

	html_content = d.parseString(convertToHtml(dom, template_node.params["unique_id"]))

	# preprocess content
	content = html_content.getContent().replace("<p></p>", "").strip()
	for key, val in HTML_ENTITIES.iteritems():
		content = content.replace(val, key)

	return (template_node, html_content)



# lame, i know..
def __removeHTMLEntities(s):
	for key, val in HTML_ENTITIES.iteritems():
		s = s.replace(key, val)

	return s



def getUserCodeboxTemplate(dom, name):
	"Check if there is node called |name|. If there is, return first codebox from that node."
	template_node, template_html = __getUserTemplate(dom, name)

	if template_node is None:
		return None
	template = template_node.find("codebox")

	if len(template) <= 0:
		return None
	template = template[0].getContent()

	template = __removeHTMLEntities(template)

	# remove whole node from document
	template_node.replaceWith(d.HTMLElement(""))

	return template


def saveUserCSS(html_template, css, out_dir):
	""""
	Save |css|.
	Try parse filename from |html_template|, if there is proper <link rel='stylesheet'> tag.
	Default "style.css".
	"""
	dom = d.parseString(html_template)
	css_name = dom.find("link", {"rel":"stylesheet"})

	if len(css_name) <= 0:
		css_name = "style.css"
	else:
		css_name = css_name[0]
		css_name = css_name.params["href"] if "href" in css_name.params else "style.css"

	css_name = os.path.basename(css_name)

	fh = open(out_dir + "/" + css_name, "wt")
	fh.write(css)
	fh.close()



# TODO: this needs to be refactored
def generateAtomFeed(dom, out_dir):
	rss_node = __getFirstNodeByCIName(dom, "__rss")

	# don't continue, if there is no rss node
	if rss_node is None:
		return None

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


	atom_template = __removeHTMLEntities(atom_template)


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
		raise ValueError("Link in your Atom template has to have 'href' parameter!")
	filename = filename.params["href"].split("/")[-1]

	if "." not in filename:
		filename = "atom.xml"
		writeln("There isn't specified filename of your feed, so I chosed default 'atom.xml'.")


	fh = open(out_dir + "/" + filename, "wt")
	fh.write(atom_feed)
	fh.close()


	# get rid of RSS node
	rss_node.replaceWith(d.HTMLElement(""))



#= Main program ================================================================
if __name__ == '__main__':
	pass