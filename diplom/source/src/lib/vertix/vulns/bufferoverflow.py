# -*- coding: utf8 -*-
# from random import randrange
from flawfinder import process_text

GENERAL_VULNERABLE_STDLIB_FUNCTIONS_LIST = (
        'strcpy',
        'strcat',
        'sprintf',
        'gets',
        'scanf',
        'memcpy',
        'memmove',
        'fputs',
        'fgets',
        'vscanf',
    )

def get_vulns_count(source,ast):
    
    # result = 0
    # for func in GENERAL_VULNERABLE_STDLIB_FUNCTIONS_LIST:
    #     result += source.lower().count(func)
    # return result
    return process_text('untitled', source)


__author__ = 'andrew.vasyltsiv'