#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
# This work is licensed under a Creative Commons 3.0
# Unported License (http://creativecommons.org/licenses/by/3.0/).
#
#= Imports ====================================================================
import sys


# this will work everywhere and exactly how i want, not like print / print()
def write(s, out=sys.stdout):
	out.write(str(s))
	out.flush()


def writeln(s, out=sys.stdout):
	write(str(s) + "\n", out)


try:
	from dhtmlparser import *
except ImportError:
	writeln("\nThis script require dhtmlparser.", sys.stderr)
	writeln("> https://github.com/Bystroushaak/pyDHTMLParser <\n", sys.stderr)
	sys.exit(1)



#= Main program ================================================================
if __name__ == '__main__':
	pass