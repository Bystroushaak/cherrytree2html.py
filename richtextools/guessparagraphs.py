#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
# This work is licensed under a Creative Commons 3.0
# Unported License (http://creativecommons.org/licenses/by/3.0/).
#
#= Imports ====================================================================
import parser as d



#= Functions ==================================================================
def unlinkFromParent(el):
	"Unlink element from parent."

	if (el.parent is not None) and (el in el.parent.childs):
		i = el.parent.childs.index(el)
		if i >= 0:
			del el.parent.childs[i]


def replaceInParent(el, new_el):
	"Replace element in parent.childs."

	if (el.parent is not None) and (el in el.parent.childs):
		el.parent.childs[el.parent.childs.index(el)] = new_el


def elementToP(el):
	"""
	Convert one element to <p>el</p>. Element is changed in parent.
	Returns element (if you don't need it, just drop it, everything is
	changed in right place in parent already.)
	"""

	p = d.HTMLElement("<p>")

	p.childs.append(el)

	# for double linked lists
	if el.parent is not None:
		p.parent  = el.parent
		replaceInParent(el, p)
		el.parent = p

	p.endtag = d.HTMLElement("</p>")

	return p


def elementsToP(els):
	"""
	Put array of elements into <p>. Result is put into els.parent, so you
	can just call this and don't care about rest.

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


def __processBuffer(buff):
	"Convert array of elements in buff to paragraphs."

	p_stack = [[]]
	for el in buff:
		content = el.getContent() if el.isTag() else str(el)

		# content without \n\n is just regular part of <p>
		if not "\n\n" in content:
			if "\n" in content:
				nel = d.parseString(str(el).replace("\n", "<br />\n"))
				nel.parent = el.parent
				el.replaceWith(nel)
			p_stack[-1].append(el)
			continue

		if el.isTag():
			__processBuffer(el.childs)
		else:
			# split by \n\n and convert it to tags
			tmp = map(
				lambda x: d.HTMLElement(x.replace("\n", "<br />\n")),  # support for <br>
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
			tmp = tmp[1:] if len(tmp) > 1 else []
			# ^ del tmp[0] <- this tends to delete object in tmp[0] .. wtf?

			# other elements are new <p>s by itself
			for i in tmp:
				p_stack.append([i])

	# convert stack of elements to <p>
	for p in p_stack:
		elementsToP(p)


def guessParagraphs(s, dont_wrap = ["h1", "h2", "h3", "pre", "center", "table"]):
	# parse string and make it double-linked tree
	node = d.parseString(s)
	d.makeDoubleLinked(node)

	# get all elements between <hx> (headers) - they will be converted to
	# <p>aragraphs
	tmp = []
	buffs = []
	for el in node.childs[0].childs:
		if el.getTagName().lower() in dont_wrap and not el.isEndTag():
			buffs.append(tmp)
			tmp = []
		else:
			tmp.append(el)
	buffs.append(tmp)

	# process paragraphs
	for buff in buffs:
		__processBuffer(buff)

	# remove blank <p>aragraphs
	map(
		lambda x: x.replaceWith(d.HTMLElement("")),
		filter(
			lambda x: x.getContent().strip() == "",
			node.find("p")
		)
	)

	# return "beautified" string
	return str(node)                               \
	                .replace("<p>", "\n<p>")       \
	                .replace("</p>", "</p>\n\n")   \
	                .replace("<p>\n", "<p>")       \
	                .replace("<h", "\n<h")         \
	                .replace("<p><br />\n", "<p>") # don't ask..



#= Main program ===============================================================
if __name__ == '__main__':
	pass
