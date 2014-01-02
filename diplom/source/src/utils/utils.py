# -*- coding: utf8 -*-

class SolutionRenderer(object):
    def __init__(self):
        self.template_dir = "templates"
        self.renderer = pystache.Renderer(file_extension="tmpl",
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