# -*- coding: utf8 -*-
#!/usr/bin/env python

import sys
sys.path.insert(0, 'lib/')

import endpoints
from app.endpoints_api import an_api

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

package ="vertix-api"

vertix_application = endpoints.api_server([an_api])


__author__ = 'andrew.vasyltsiv'