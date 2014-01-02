# -*- coding: utf8 -*-

import sys
sys.path.insert(0, 'lib/')

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from utils.utils import SolutionRenderer, get_translation

an_api = endpoints.api(
        name='libvertix',
        version='v1.0',
        description="Vertix API"
    )

#Definig the API default types of messages

#testEcho

class EchoRequest(messages.Message):
    message = messages.StringField(1)

class EchoResponse(messages.Message):
    message = messages.StringField(1)

@an_api.api_class(
        resource_name="echo",
        path="echo"
    )
class Echo(remote.Service):
    @endpoints.method(
            EchoRequest,
            EchoResponse
        )
    def echo(self,request):
        return EchoResponse(message=request.message)

@an_api.api_class(
        resource_name="echo2",
        path="echo2"
    )
class Echo2(remote.Service):
    @endpoints.method(
            EchoRequest,
            EchoResponse
        )
    def echo2(self,request):
        return EchoResponse(message=request.message)


__author__ = 'andrew.vasyltsiv'