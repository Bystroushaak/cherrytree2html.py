#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
# This work is licensed under a Creative Commons 3.0
# Unported License (http://creativecommons.org/licenses/by/3.0/).
#
#= Imports ====================================================================
import sys
import shutil
import base64
import hashlib
import os.path


import parser as d
from parser import writeln
from getnodepath import *
from guessparagraphs import *


#= Variables ==================================================================
# do not wrap theese with <p>
DONT_WRAP = [
    "h1",
    "h2",
    "h3",
    "pre",
    "center",
    "table"
]


#= Functions & objects ========================================================
def _transformLink(tag, dom, node_id, out_dir, root_path):
    """
    Transform <rich_text link="webs http://kitakitsune.org">odkaz</rich_text>
    to <a href="http://kitakitsune.org">odkaz</a>.

    Also some basic link handling, ala local links and links to other nodes.
    """

    if "link" in tag.params:
        el = d.HTMLElement("<a>")
        el.childs = tag.childs

        # cherrytree puts string "webs "/"node " before every link for some
        # reason
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
        elif tag.params["link"].startswith("file "):
            link = base64.b64decode(tag.params["link"].split()[1])

            # support for local images - I did tried to make it work as node,
            # but that failed miserably, because there is limit to picture
            # dimensions and other shitty crap
            file_type = link.split(".")
            pic_types = ["png", "gif", "jpg", "jpeg"]
            if len(file_type) >= 1 and file_type[-1].lower() in pic_types:
                directory = out_dir + "/pictures"
                if not os.path.exists(directory):
                    os.makedirs(directory)

                local_name = "%s/%s_%s" % (
                    directory,
                    hashlib.md5(link).hexdigest(),
                    os.path.basename(link)
                )

                shutil.copyfile(link, local_name)
        elif tag.params["link"].startswith("node "):
            # internal links contains only node id
            link_id = link.strip()

            # get nodename
            linked_nodename = dom.find("node", {"unique_id": str(link_id)})
            if not linked_nodename:
                writeln("Broken link to node ID '" + link_id + "'", sys.stderr)
                link = "[broken link to internal node]"
            else:
                # get (this) node depth
                depth = len(getNodePath(dom, node_id).split("/")) - 1
                link = "./" + (depth * "../") + getNodePath(dom, link_id)

        el.params["href"] = link.strip()

        el.endtag = d.HTMLElement("</a>")
        tag.replaceWith(el)


def _transformRichText(tag):
    "Transform tag ala <rich_text some='crap'> to real html tags."

    # skip richtext nodes with no parameters (they are removed later)
    if not tag.params:
        return

    # tags which contains nothing printable are converted just to its content
    # (whitespaces) "<h3> </h3>" -> " "
    if not tag.getContent().strip():
        tag.params = {}
        return

    rich_text_table = [
        {"attr_key": "weight",        "attr_val": "heavy",     "tag": "strong"},
        {"attr_key": "style",         "attr_val": "italic",    "tag": "i"},
        {"attr_key": "underline",     "attr_val": "single",    "tag": "u"},
        {"attr_key": "strikethrough", "attr_val": "true",      "tag": "del"},
        {"attr_key": "family",        "attr_val": "monospace", "tag": "tt"},
        {"attr_key": "scale",         "attr_val": "h1",        "tag": "h1"},
        {"attr_key": "scale",         "attr_val": "h2",        "tag": "h2"},
        {"attr_key": "scale",         "attr_val": "h3",        "tag": "h3"},
        {"attr_key": "scale",         "attr_val": "sup",       "tag": "sup"},
        {"attr_key": "scale",         "attr_val": "sub",       "tag": "sub"},
        {"attr_key": "scale",         "attr_val": "small",     "tag": "small"},
        {"attr_key": "justification", "attr_val": "center",    "tag": "center"},
        {"attr_key": "justification", "attr_val": "left",      "tag": None},
    ]

    def has_same_value(tag, trans):
        return tag.params[trans["attr_key"]] == trans["attr_val"]

    # transform tags
    for trans in rich_text_table:
        if trans["attr_key"] in tag.params and has_same_value(tag, trans):
            del tag.params[trans["attr_key"]]

            if trans["tag"]:
                # put HTML tag INTO rich_text
                el = d.HTMLElement("<" + trans["tag"] + ">")
                el.params = trans.get("params", {})
                el.childs = tag.childs
                tag.childs = [el]
                el.endtag = d.HTMLElement("</" + trans["tag"] + ">")


def _processTable(table):
    "Convert cherrytree table to HTML table."

    del table.params["char_offset"]

    html_table = str(table)

    html_table = html_table.replace("<cell>", "<td>")
    html_table = html_table.replace("</cell>", "</td>")
    html_table = html_table.replace("<row>", "<tr>")
    html_table = html_table.replace("</row>", "</tr>\n")

    return d.parseString(html_table)


def _processPicture(picture, out_dir, root_path):
    content = base64.b64decode(picture.getContent())

    if out_dir is not None:
        filename = hashlib.md5(content).hexdigest() + ".png"

        directory = out_dir + "/pictures"
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(directory + "/" + filename, "wb") as f:
            f.write(content)

    img = d.HTMLElement("<img />")

    if out_dir is not None:
        img.params["src"] = root_path + "/pictures/" + filename
    else:
        content = "".join(picture.getContent().split())
        img.params["src"] = "data:image/png;base64," + picture.getContent()

    return img


def _createReplacements(node, out_dir, root_path):
    """
    Create html versions of `replacements_tagnames` tags and put them into
    `replacements[]` variable. Remove `replacements_tagnames` from DOM.

    Transform <codebox>es to <pre> tags.

    CherryTree saves <codebox>es at the end of the <node>. Thats right - they
    are not in the source as all other tags, but at the end. Instead of
    <codebox> in the text, there is
    <rich_text justification="left"></rich_text>, which needs to be replaced
    with <pre>
    """
    def in_replacements_tagnames(x):
        return x.getTagName().lower() in ["codebox", "table", "encoded_png"]

    replacements = []
    for replacement in node.find("", fn=in_replacements_tagnames):
        el = None

        tag_name = replacement.getTagName()
        if tag_name == "codebox":
            el = d.HTMLElement("<pre>")
            el.childs = replacement.childs[:]
            el.params["syntax"] = replacement.params["syntax_highlighting"]
            el.endtag = d.HTMLElement("</pre>")
        elif tag_name == "table":
            el = _processTable(replacement)
        elif tag_name == "encoded_png":
            el = _processPicture(replacement, out_dir, root_path)
        else:
            raise ValueError(
                "This shouldn't happend." +
                "If does, there is new unknown <element>."
            )

        replacements.append(el)

        # remove original element (codebox/table) from DOM
        replacement.replaceWith(d.HTMLElement(""))

    return replacements


def convertToHtml(dom, node_id, do_anchors=True, out_dir=None, root_path=None):
    # get node element
    node = dom.find("node", {"unique_id": str(node_id)})[0]
    node = d.parseString(str(node)).find("node")[0]  # get deep copy

    # remove subnodes
    for n in node.find("node"):
        if n.params["unique_id"] != str(node_id):
            n.replaceWith(d.HTMLElement(""))

    replacements = _createReplacements(node, out_dir, root_path)

    def find_replacements_placeholder(node):
        return node.find(
            "rich_text",
            {"justification": "left"},
            fn=lambda x: x.getContent() == ""
        )

    # replace <rich_text justification="left"></rich_text> with tags from
    # `replacements`
    for cnt, rt in enumerate(find_replacements_placeholder(node)):
        if "link" in rt.params:  # support for pictures as links
            el = d.HTMLElement("<rich_text>")
            el.params["link"] = rt.params["link"]
            el.childs = [replacements[cnt]]
            el.endtag = d.HTMLElement("</rich_text>")
            rt.replaceWith(el)
        else:
            rt.replaceWith(replacements[cnt])
    #===========================================================================

    # transform all <rich_text> tags to something usefull
    for t in node.find("rich_text"):
        # transform <rich_text some="crap"> to html tags
        _transformRichText(t)

        # transform links
        _transformLink(t, dom, node_id, out_dir, root_path)

        # there are _arrays_ of rich_text with no params - this is not same as
        # <p>, because <p> allows nested parameters -> <p>Xex <b>bold</b></p>,
        # but cherry tree does shit like
        # <rich_text>Xex </rich_text><rich_text weight="heavy">bold</rich_text>
        # <rich_text></rich_text>
        if len(t.params) == 0:
            el = d.HTMLElement()
            el.childs = t.childs
            t.replaceWith(el)

    # convert text to paragraphs
    node = str(node).replace('<rich_text justification="left">', "")  # dont ask
    node = d.parseString(guessParagraphs(node, DONT_WRAP))

    if do_anchors:
        # apply anchors
        for head in node.find("h1") + node.find("h2") + node.find("h3"):
            anchor = "anchor_%s_%s" % (
                head.getTagName(), utfToFilename(head.getContent())
            )

            head.params["id"] = anchor

            # make head link to itself
            head.childs = [
                d.parseString(
                    "<a href='#" + anchor + "'>" + head.getContent() + "</a>"
                )
            ]

    return str(node.find("node")[0].getContent())
