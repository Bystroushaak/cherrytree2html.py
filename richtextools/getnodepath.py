#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
# This work is licensed under a Creative Commons 3.0
# Unported License (http://creativecommons.org/licenses/by/3.0/).
#
#= Imports ====================================================================
import os.path
import unicodedata
from string import maketrans


import parser as d


#= Functions & objects ========================================================
def utfToFilename(nodename):
    "Convert UTF nodename to ASCII."

    intab = """ ?,@#$%^&*{}[]'"><°~\\|\t"""
    outtab = """_!!!!!!!!!!!!!!!!!!!!!!!"""
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
    node = dom.find("node", {"unique_id": str(nodeid)})[0]

    # check for filename in tags
    new_filename = None
    if "tags" in node.params and node.params["tags"].strip() != "":  # if tags are in node definition
        for i in node.params["tags"].split():                        # go thru tags
            if i.startswith("filename:"):                            # look for tag which starts with filename:
                i = i.split(":")
                new_filename = i[1] if len(i) > 1 else None
                break

    # does this node contain another nodes?
    endpoint = len(node.find("node")) <= 1

    # get path (based on node path in dom)
    path = ""
    while node.parent is not None and node.getTagName().lower() == "node":
        path = node.params["name"] + "/" + path
        node = node.parent

    if endpoint:
        path = path[:-1]  # remove '/' from end of the path
    else:
        path += "index"   # index file for directory
    path += ".html"

    # apply new_filename from from tags parameter of node
    if new_filename is not None:
        path = os.path.dirname(path)
        path += "/" if path.strip() != "" else ""
        path += new_filename

    return utfToFilename(path)
