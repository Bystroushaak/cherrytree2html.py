#!/usr/bin/env python
# -*- coding: utf-8 -*-
__version = "1.2.0"
__date    = "25.08.2013"
__author  = "Bystroushaak"
__email   = "bystrousak@kitakitsune.org"
# 
# Interpreter version: python 2.7
# This work is licensed under a Creative Commons 3.0 
# Unported License (http://creativecommons.org/licenses/by/3.0/).
# Created in Sublime text 2 editor.
#
#= Imports =====================================================================
import parser as d
from savenode        import saveNode, COPYRIGHT
from converttohtml   import convertToHtml

from usertemplates import saveUserCSS
from usertemplates import generateAtomFeed
from usertemplates import getUserCodeboxTemplate
from usertemplates import removeSpecialNodenames



#= Main program ================================================================
if __name__ == '__main__':
	pass