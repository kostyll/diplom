# -*- coding: utf8 -*-
# from random import randrange
from holsted import Holsted

def get_jilb(source,ast):

    # TODO
    # return  (randrange(0,5)*randrange(2,12))
    try:
        result_holsted = Holsted(source).run()
        result = {
            'Rup': result_holsted['E_inteligence_try_level']
        }
        for key in result.keys():
            result[key] = round(result[key],2)
        return result.values()[0]/100.0
    except:
        return -1

__author__ = 'andrew.vasyltsiv'