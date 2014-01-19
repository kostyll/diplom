# -*- coding: utf8 -*-
#!/usr/bin/env python

import sys
sys.path.insert(0, 'lib/')

import gettext
import webapp2

from app.rest import (
        Echo,
        Main,
        UploadHandler,
        ServeHandler,
        ListProjectsHandler,
        ListProjectFilesSLOC,
        ListProjectFilesp,
        ProjectHandler,
        GetCodeHandler,
        SignVulnerability,
        UnSignVulnerability,
        ExploitVulnerability,
        TestCode,
    )


def application():
    vertix_application = webapp2.WSGIApplication(
        [
            ('/echo', Echo),
            ('/upload', UploadHandler),
            ('/serve/([^/]+)?', ServeHandler),
            ('/projects/', ListProjectsHandler),
            ('/ajax/file/([^/]+)?/', GetCodeHandler),
            ('/projects/([^/]+)?/',ProjectHandler),
            ('/ajax/project/([^/]+)?/SLOC/',ListProjectFilesSLOC),
            ('/ajax/project/([^/]+)?/p/',ListProjectFilesp),
            ('/ajax/sign/([^/]+)?/', SignVulnerability),
            ('/ajax/unsign/([^/]+)?/', UnSignVulnerability),
            ('/ajax/exploit/([^/]+)?/', ExploitVulnerability),
            ('/',Main),
            ('/test/',TestCode)
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