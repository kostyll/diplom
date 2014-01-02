# -*- coding: utf8 -*-
#!/usr/bin/env python

import sys
sys.path.insert(0, 'lib/')

import gettext
import webapp2

class Echo(webapp2.RequestHandler):
    def get(self):
        message = self.request.get('message')
        self.response.write(message)


def application():
    vertix_application = webapp2.WSGIApplication(
        [
            ('/echo', Echo),
        ]
        ,debug=True)
    vertix_application.translations = {}
    # for lang in ['en','ru','ua']:
    #     vertix_application.translations[lang] = gettext.translation(
    #             'vertix', localedir='i18n',languages=[lang]
    #         )
    return vertix_application

vertix_application = application()

__author__ = 'andrew.vasyltsiv'