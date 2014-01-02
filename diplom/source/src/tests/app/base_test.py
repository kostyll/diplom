# -*- coding: utf8 -*-
from tests.abstract import BasicTestCase
import json

class testsRest(BasicTestCase):
    def testEcho(self):
        response = self.testapp.get('/echo',{'message':"Vertix"})
        self.assertEqual(response.body, 'Vertix') 


class testEndpoints(BasicTestCase):
    def testEndpointsEcho(self):
        message = '3'
        try:
            print list(method for method in dir(self.testapi) if not method.startswith('_'))
        except Exception,e:
            print "error",e
        jsondata = json.loads(self.testapi.echo().echo(body={'message':message}).body)
        self.assertEqual(jsondata['message'], message)

__author__ = 'andrew.vasyltsiv'