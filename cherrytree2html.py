#!/usr/bin/env python
# -*- coding: utf-8 -*-
__name    = ".ctd to .html convertor"
__author  = "Bystroushaak"
__email   = "bystrousak@kitakitsune.org"
#
# Interpreter version: python 2.7
# This work is licensed under a Creative Commons 3.0
# Unported License (http://creativecommons.org/licenses/by/3.0/).
# Created in Sublime text 2 editor.
#
#= Imports ====================================================================
import os
import re
import sys
import urllib

import os.path
import argparse


# splitted into smaller modules to prevent bloating
from richtextools import *


#= Variables ==================================================================
OUT_DIR = "output"


#= Functions & objects ========================================================
def printVersion():
    writeln(
        "%s by %s (%s)" % (__name, __author, __email)
    )


def listNodes(dom):
    "Return list of nodes and their IDs."

    ids = []
    nodes = ""
    for node in dom.find("node"):
        nodes += node.params["unique_id"].ljust(4) + "- " + node.params["name"]
        nodes += "\n"
        ids.append(int(node.params["unique_id"]))

    return ids, nodes


def rawXml(dom, node_id, do_anchors=None):
    "Just return node XML source."

    # get node element
    node = dom.find("node", {"unique_id": str(node_id)})[0]

    # remove subnodes
    for n in node.find("node"):
        if n.params["unique_id"] != str(node_id):
            n.replaceWith(d.HTMLElement(""))

    return str(node)


def _read_resource(path):
    """Try open and read data from given location."""
    if os.path.exists(path):
        with open(args.filename) as f:
            return f.read()

    return urllib.urlopen(path).read()


#= Main program ===============================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filename",
        metavar="FN",
        action="store",
        default="",
        type=str,
        nargs="?",
        help="Filename."
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="Print version."
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        default=False,
        help="List names of all nodes."
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        default=False,
        help="Interactive mode - select node and convert it to HTML."
    )
    parser.add_argument(
        "-s",
        "--save",
        action="store_true",
        default=False,
        help="Save to file named [nodeid]_[ascii_nodename].html."
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        default=False,
        help="Save all nodes to HTML."
    )
    parser.add_argument(
        "-n",
        "--node",
        metavar="NODE ID",
        action="store",
        type=int,
        default=-1,
        help="Print converted node to stdout."
    )
    parser.add_argument(
        "-r",
        "--raw",
        action="store_true",
        default=False,
        help="Print raw node source code (XML)."
    )
    parser.add_argument(
        "--do-anchors",
        action="store_true",
        default=False,
        help="Put <h> anchors to the code."
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
    try:
        data = _read_resource(args.filename)
    except IOError:
        writeln("Can't read '" + args.filename + "'!", sys.stderr)
        sys.exit(2)

    def replace_strange_formatting(data):
        return re.sub("\n\t+<rich_text", "<rich_text", data)
        # return data.replace("\n\t\t<rich_text", "<rich_text")

    # read cherrytree file and parse it to the DOM
    dom = d.parseString(replace_strange_formatting(data))

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
        while selected is not True:
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
            nodename = saveNode(
                dom,
                nodeid,
                savenode.HTML_TEMPLATE,
                OUT_DIR,
                do_anchors=args.do_anchors
            )

            writeln("\nSaved to '" + nodename + "'")
        else:
            writeln(convertToHtml(dom, str(nodeid)))

    elif args.all:
        if not os.path.exists(OUT_DIR):
            os.makedirs(OUT_DIR)

        # remove nodes which names starts with __ (with exception of
        # usertemplates.SPECIAL_NODENAMES)
        removeSpecialNodenames(dom)

        generateAtomFeed(dom, OUT_DIR)

        # check if there is user's own html template - if so, use it
        html_template = savenode.HTML_TEMPLATE
        template = getUserCodeboxTemplate(dom, "__template")
        if template is not None:
            html_template = template

        # check for user's css style
        css = getUserCodeboxTemplate(dom, "__css")
        if css is not None:
            saveUserCSS(html_template, css, OUT_DIR)

        # convert all nodes to html
        for n in dom.find("node"):
            nodename = saveNode(
                dom,
                nodeid=n.params["unique_id"].strip(),
                html_template=html_template,
                out_dir=OUT_DIR,
                name=n.params["name"],
                do_anchors=args.do_anchors
            )

            writeln("Node '" + nodename + "' saved.")

        sys.exit(0)

    # convert selected node identified by nodeid in args.node
    elif args.node != -1:
        ids = listNodes(dom)[0]

        if args.node not in ids:
            writeln(
                "Selected ID '" + str(args.node) + "' doesn't exists!",
                sys.stderr
            )
            sys.exit(3)

        if args.save:
            nodename = saveNode(
                dom,
                nodeid=args.node,
                html_template=savenode.HTML_TEMPLATE,
                out_dir=OUT_DIR,
                do_anchors=args.do_anchors
            )

            writeln("Saved to '" + nodename + "'")
        else:
            writeln(convertToHtml(
                dom, args.node,
                do_anchors=args.do_anchors
            ))
            writeln(COPYRIGHT)
