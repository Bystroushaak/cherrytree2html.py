#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
# This work is licensed under a Creative Commons 3.0
# Unported License (http://creativecommons.org/licenses/by/3.0/).
#
#= Imports ====================================================================
import os.path
from string import Template


from getnodepath   import getNodePath
from converttohtml import convertToHtml



#= Variables ==================================================================
HTML_TEMPLATE = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<HTML>
<head>
	<title>$title</title>

	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />

	<link rel="stylesheet" type="text/css"             href="$rootpath/style.css" />
	<link rel="alternate"  type="application/atom+xml" href="atom.xml" />
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



#= Functions & objects ========================================================
def saveNode(dom, nodeid, html_template, out_dir, name = None, do_anchors = True):
	"Convert node to the HTML and save it to the HTML."

	nodeid   = str(nodeid)
	filename = getNodePath(dom, nodeid)

	rootpath = filename.count("/") * "../"
	rootpath = rootpath[:-1] if rootpath.endswith("/") else rootpath
	rootpath = "." if rootpath == "" else rootpath

	# ugly, bud increase parsing speed a bit
	if name is None:
		name = dom.find("node", {"unique_id": nodeid})[0]
		name = name.params["name"]

	# generate filename, convert html
	data = convertToHtml(dom, nodeid, do_anchors = do_anchors)

	# apply html template
	data = Template(html_template).substitute(
		content   = data,
		title     = name,
		copyright = COPYRIGHT,
		rootpath  = rootpath
	)

	# check if directory tree exists - if not, create it
	directory = out_dir + "/" + os.path.dirname(filename)
	if not os.path.exists(directory):
		os.makedirs(directory)

	fh = open(out_dir + "/" + filename, "wt")
	fh.write(data)
	fh.close()

	return filename



#= Main program ===============================================================
if __name__ == '__main__':
	pass
