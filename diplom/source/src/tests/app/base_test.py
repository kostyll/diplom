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
            resources = list(resource for resource in dir(self.testapi) if not resource.startswith('_'))
            print resources
            for resource in resources:
                exec('rdir = dir(self.testapi.%s())'% resource)
                print "resource=%s"%resource,rdir
                methods = list(method for method in rdir if not method.startswith("_"))
                print "methods",methods
        except Exception,e:
            print "error",e
        result = self.testapi.echo().echo(body={'message':message}).execute()
        self.assertEqual(result['message'], message)
        self.assertEqual(1, 2)

__author__ = 'andrew.vasyltsiv'