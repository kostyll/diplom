# -*- coding: utf8 -*-

import unittest
import webtest
from google.appengine.ext.testbed import Testbed
from main import application

from httplib2 import Http
http = Http(None)

from apiclient.discovery import build
service = build("libvertix", "v1.0", http=http, 
  discoveryServiceUrl=("http://localhost:8080/_ah/api/discovery/v1/"
                       "apis/libvertix/v1.0/rest"))

class BasicTestCase(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        #self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.testapp = webtest.TestApp(application())

        self.testapi = service



    def tearDown(self):
        self.testbed.deactivate()



__author__ = 'andrew.vasyltsiv'
