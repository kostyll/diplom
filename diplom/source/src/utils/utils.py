# -*- coding: utf8 -*-

import zipfile
from zipfile import ZipFile
from StringIO import StringIO
import pystache

# zip = zipfile.ZipFile('Vulnserver.zip')
# files = zip.namelist
# c_files = map(
#     lambda x: {x: zip.open(x).read()} , 
#     list(file for file in files() if file.endswith('.c'))
#     )
# h_files = map(
#     lambda x: {x: zip.open(x).read()} , 
#     list(file for file in files() if file.endswith('.h'))
#     )

# file_like_obj = StringIO(open('Vulnserver.zip','rb').read())
# zip = zipfile.ZipFile(file_like_obj)
# files = zip.namelist()
# c_files = map(
#     lambda x: {x: zip.open(x).read()} , 
#     list(file for file in files if file.endswith('.c'))
#     )
# h_files = map(
#     lambda x: {x: zip.open(x).read()} , 
#     list(file for file in files if file.endswith('.h'))
#     )

def get_project_files(source):
    try:
        if source[:2] != 'PK':  # not zip magic
            return {'project':{'untitled':source}, 'error':False}
        else:
            file_like_obj = StringIO(source)
            zip = ZipFile(file_like_obj)
            files = zip.namelist()
            project_files = map(
                lambda x: {x: zip.open(x).read()} , 
                list(file for file in files if (file.endswith('.c') or (file.endswith('.h')))
                ))
            return {'project':project_files, 'error':False}
    except Exception, e:
        print e
        return {'error':True}


class SolutionRenderer(object):
    def __init__(self):
        #self.template_dir = "templates"

        self.renderer = pystache.Renderer(file_extension="html",
                                          search_dirs="templates/",
                                          file_encoding='utf-8', partials=self)

    def get(self, partial):
        print partial
        print self.renderer.context
        return ""

    def render(self, template, context=None):
        return self.renderer.render_name(template, context)


# def render_steps(html,html_flat,lang):
#     _ = get_translation(lang)
#     f = SolutionRenderer()
#     templates = {
#                      'step_header': _('Step %current of %count'),
#                      'solution': _('Solution'),
#                      'next_step': _('Next step'),
#                      'show_all': _('Show all'),
#                      'hide_all': _('Hide all')
#         }
#     return f.render('steps',
#                             {'steps': html,
#                              'flat_steps': html_flat,
#                              'templates': templates}
#                             )

def get_translation(lang='en'):
    translations = {}
    translations[lang] = gettext.translation(
        'vertix', localedir='i18n', languages=[lang])
    return translations[lang].ugettext 


__author__ = 'andrew.vasyltsiv'