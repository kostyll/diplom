# -*- coding: utf8 -*-
# from random import randrange
from holsted import Holsted

def get_mackkeib(source,ast):

    #TODO
    # return randrange(2,14)*randrange(3,20)
    try:
        result_holsted = Holsted(source).run()
        result = {
            'Z(g)': result_holsted['S_difficaltcy']
        }
        for key in result.keys():
            result[key] = round(result[key],2)
        return result.values()[0]
    except:
        return -1

__author__ = 'andrew.vasyltsiv'