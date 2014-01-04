# -*- coding: utf8 -*-

from pycparser.c_parse import CParser

def get_ast_from_text(source):
    return CParser().parse(source)

def get_ast_from_file(filename):
    return CParser().parse(open(filename,'rU').read())

def get_ast_from_StringIO(source):
    return CParser().parse(source.read())

__author__ = 'andrew.vasyltsiv'