#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
#
"""
Picture localizer.

This script allows you to move all pictures referenced in HTML document into
the same directory as the HTML document.

It is useful, if you need to upload the document somewhere with all the pictures
from the internet/your disk.
"""
#= Imports ====================================================================
import sys
import shutil
import os.path
from md5 import md5

from httpkie import Downloader
import dhtmlparser as d


#= Variables ==================================================================
ALLOWED_IMAGES = [
    "jpg",
    "jpeg",
    "gif",
    "png"
]


#= Functions & objects ========================================================
def localize_image(path, out_dir):
    new_path = out_dir + "/" + os.path.basename(path)

    if os.path.exists(new_path):
        path_md5 = md5(open(path).read()).hexdigest()
        new_path_md5 = md5(open(new_path).read()).hexdigest()

        if path_md5 != new_path_md5:
            while os.path.exists(new_path):
                suffix = new_path.rsplit(".", 1)[1]
                new_path = md5(os.path.basename(new_path)).hexdigest()
                new_path = out_dir + "/" + new_path + "." + suffix

    if not os.path.exists(new_path):
        if path.startswith("http://") or path.startswith("https://"):
            with open(new_path, "wb") as f:
                f.write(Downloader().download(path))
        else:
            shutil.copy(path, new_path)

    return "./" + os.path.basename(new_path)


#= Main program ===============================================================
if __name__ == '__main__':
    if len(sys.argv) == 1 or not os.path.exists(sys.argv[1]):
        sys.stderr.write(
            "Image localizer\nUsage:\n\t%s file.html\n" % sys.argv[0]
        )
        sys.exit()
    abs_path = os.path.abspath(sys.argv[1])

    data = None
    with open(abs_path) as f:
        data = f.read()

    dom = d.parseString(data)

    # get name for the output directory
    out_dir = dom.find("title")
    if out_dir:
        out_dir = out_dir[0].getContent().strip().replace("/", "")
    else:
        out_dir = os.path.basename(sys.argv[1])

    # create output directory
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    # localize inlined images
    for img in dom.find("img"):
        if "src" not in img.params:
            continue

        img.params["src"] = localize_image(img.params["src"], out_dir)

    # localize linked images
    for a in dom.find("a"):
        if "href" not in a.params or "." not in a.params["href"]:
            continue

        if a.params["href"].rsplit(".", 1)[1].lower() not in ALLOWED_IMAGES:
            continue

        a.params["href"] = localize_image(a.params["href"], out_dir)

    with open(out_dir + "/" + os.path.basename(abs_path), "wt") as f:
        f.write(str(dom))
