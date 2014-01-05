from __future__ import unicode_literals
# -*- coding: utf8 -*-

import webapp2
from copy import deepcopy
from utils.utils import SolutionRenderer

import os
import urllib

from google.appengine.ext import blobstore
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from app.models import (
        Project,
        SourceFile,
        Metrix,
        Vulnerability
    )

from utils.utils import (
        get_project_files
    )

projects = Project.all()

upload_url = blobstore.create_upload_url('/upload')

ALL_ITEMS = [
    'title',
    'head_main',
    'head_projects',
    'search_query',
    'search_button',
    'head_main',
    'head_projects',
    'head_project',
    'head_file',
    'path_title',
    'path_content',
    'content_description',
    'content_chart',
    'chart_title',  
    'items',
]

GENERAL_ITEMS = {
    'title' : 'Пошук вразливостей',
    'search_query' : 'ключове слово',
    'search_button' : 'Пошук',
    'head_main' : 'Головна',
    'head_projects' : 'Список проектів',
    'path_title' : 'Шлях',    
    'upload_button':"Завантажити", 
    'head_file_upload':'Завантаження проекту',
    'head_file_search':'Пошук',
    'upload_url':upload_url,
}

CONTEXT_ITEMS = {
    'head_project':"Проект",
    'head_file':"Файл",  
    'path_content':"Шлях до контенту", 
    'content_description':"характеристики контенту",
    'content_chart':"Дані для графіків",
    'chart_title':"Діаграма",
    'head_metrix_holsted':'Метрика Холстеда',
    'head_metrix_mackkeib':'Метрика Маккейба',
    'head_metrix_jilb':'Метрика Джилба',
    'head_vulns':'Кі-сть потенційних вразливостей',
    'projects': projects,
}

def process_path(path):
    return map(lambda x: x.encode(),map(str, path))

def process_template_imems():
    templates = deepcopy(GENERAL_ITEMS)
    templates.update(CONTEXT_ITEMS)
    return templates

def process_template_path(templates,path):
    templates.update({'path_content':process_path(path)})

class Echo(webapp2.RequestHandler):
    def get(self):
        message = self.request.get('message')
        self.response.write(message)


class Main(webapp2.RequestHandler):
    def get(self):
        f = SolutionRenderer()
        templates = process_template_imems()
        path = ['2',3,4.5]
        process_template_path(templates, path)
        return self.response.write(f.render('index',templates))


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
        blob_info = upload_files[0]
        self.redirect('/serve/%s' % blob_info.key())
        #self.redirect('/')


class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        uploaded_file = blob_info.open().read()
        project_files = get_project_files(uploaded_file) 
        # print dir(blob_info)
        project_name = blob_info.filename
        project = Project(
                name = project_name
            )
        project.put()
        if project_files['error'] == False:
            if isinstance(project_files['project'], (tuple,list)):
                for item in project_files['project']:
                    source_name = item.items()[0][0]
                    # print source_name
                    source_content = item.items()[0][1]
                    # print source_content
                    source_file = SourceFile(
                            name = source_name,
                            source = source_content,
                            project = project
                        )
                    source_file.put()
            else:
                source_content = project_files['project']['untitled']
                source_file = SourceFile(
                        name = project_name,
                        source = source_content,
                        project = project
                    )
                source_file.put()

        # self.send_blob(blob_info)
        return self.redirect('/')



class ListProjectsHandler(webapp2.RequestHandler):
    def get(self):
        for project in projects:
            print "project",project.name
        f = SolutionRenderer()
        templates = process_template_imems()
        path = []
        process_template_path(templates, path)
        templates.update({'projects':projects, 'items':projects})
        return self.response.write(f.render('index',templates))


__author__ = 'andrew.vasyltsiv'