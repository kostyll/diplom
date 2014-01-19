from __future__ import unicode_literals
# -*- coding: utf8 -*-

import webapp2
from copy import deepcopy
from utils.utils import SolutionRenderer

import os
import urllib
import json

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

from app.core import SourceProcessor

projects_list = Project.all()
# projects = map(lambda index, x: x.index = index, enumerate(projects))
projects = projects_list
# for index, x in enumerate(projects):
#     x.index = index
#     projects.append[x]

# for x in projects:
#     print x.index

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
    'head_metrix_sloc':'Метрика SLOC',
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
        project_name = str(blob_info.filename)
        processor = SourceProcessor(project_files, project_name)

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
        # global projects
        # data_projects = []
        # for project in projects:
        #     prj_name = project.name
        #     sources = SourceFile.get_by_key_name('project',project)
        #     print sources

        templates.update({'projects':projects, 'items':projects})
        return self.response.write(f.render('index',templates))

def make_nodes_hier(nodelist,root_name):
    root = {
        'name':root_name,
        'size':0
    }
    def insert_node(path,node):
        node_path = path.split('/')
        start = root
        for path_item in node_path:
            if not start.has_key('children'):
                start['children'] = [
                                        {
                                            'name':path_item,
                                            'size':0,
                                            'language':'c'
                                         }
                                        ]
            search_index = -1
            for index, item in enumerate(start['children']):
                if item['name'] == path_item:
                    search_index = index
                    break
            if search_index != -1:
                start = start['children'][search_index]
            else:
                newitem = {
                            'name':path_item,
                            'size':0,
                            'language':'c'
                            }
                start['children'].append(newitem)
                start = newitem
        if not start.has_key('children'):
            start['children'] = [node]
        else:
            start['children'].append(node)
        # item_paths = []

        start = root
        start['size'] += node['size']

        for path_item in node_path:
            for index, item in enumerate(start['children']):
                if item['name'] == path_item:
                    break
            start = start['children'][index]
            start['size'] += node['size']


        # for index, item in enumerate(node_path):
        #     for children_index, children in  enumerate(start['children']):
        #         if children['name'] == item:
        #             break
            
        #     item_paths.append(
        #             {
        #                 'num':index,
        #                 'link': start['children'][children_index]
        #             }
        #         )
        #     start = start['children_index'][children_index]
        # reversed_path = item_paths
        # reversed_path.reverse()
        # for item in reversed_path


    for item in nodelist:
        path, dummy, filename = item['name'].rpartition('/')
        node = {
            'name':filename,
            'size':item['size'],
            'language':'c'
        }
        insert_node(path, node)
    return root


class ListProjectFilesSLOC(webapp2.RequestHandler):
    def get(self,project_name):
        print repr(project_name)

        project = Project.get_by_key_name('name='+project_name)

        source_files = SourceFile.all().filter('project =',project)
        for file in source_files:
            print file
        # print "source_files",source_files

        files = map(lambda x: {'name':x.name,'size':int(x.metrix.sloc)}, source_files)
        # print 'files',files

        files = make_nodes_hier(files, project_name)
        result = json.dumps(files)
        print "result",result
        # print 'node_arch',files
        self.response.headers['Content-Type'.encode()] = 'application/json'.encode()
        self.response.out.write(result)
        # self.response.content_type = 'application/json'.encode()
        # json.dump(result, self.response.out)


class ListProjectFilesp(webapp2.RequestHandler):
    def get(self,project_name):
        print repr(project_name)

        project = Project.get_by_key_name('name='+project_name)

        source_files = SourceFile.all().filter('project =',project)
        for file in source_files:
            print file
        # print "source_files",source_files

        files = map(lambda x: {'name':x.name,'size':int(x.p*100)}, source_files)
        # print 'files',files

        files = make_nodes_hier(files, project_name)
        result = json.dumps(files)
        print "result",result
        # print 'node_arch',files
        self.response.headers['Content-Type'.encode()] = 'application/json'.encode()
        self.response.out.write(result)


class GetCodeHandler(webapp2.RequestHandler):
    def get(self, filehash):
        print filehash
        code = SourceFile.all().filter('short',filehash)[0]
        #print code.source
        self.response.write(code.source)
        return



class ProjectHandler(webapp2.RequestHandler):
    def get (self,project_name):
        project = Project.get_by_key_name('name='+project_name)
        source_files = SourceFile.all().filter('project =',project)

        path = [project_name]

        f = SolutionRenderer()
        templates = process_template_imems()
        process_template_path(templates, path)

        templates.update({
                'files': source_files,
                'projects': projects,
                'path': path,
                'project': project_name
            })
        return self.response.write(f.render('project',templates))


#recalcs projects p
def recalc_p (source_file,):
    if source_file.p > source_file.project.p :
        source_file.project.p = source_file.p
        source_file.put()


class SignVulnerability(webapp2.RequestHandler):
    def get (self,filehash):
        source_file = SourceFile.all().filter('short',filehash)[0]
        source_file.p = 0.7
        source_file.put()
        recalc_p(source_file)


class UnSignVulnerability(webapp2.RequestHandler):
    def get (self,filehash):
        source_file = SourceFile.all().filter('short',filehash)[0]
        source_file.p = 0.0
        source_file.put()
        recalc_p(source_file)


class ExploitVulnerability(webapp2.RequestHandler):
    def get (self,filehash):
        source_file = SourceFile.all().filter('short',filehash)[0]
        source_file.p = 1.0
        source_file.put()
        recalc_p(source_file)


class TestCode(webapp2.RequestHandler):
    def get(self):
        """
        In [2]: table = interpolation.LinearInterpolation(
           ...: x_index=(2,3,4),
           ...: values=(4,6,8),
           ...: extrapolate=True)

        In [3]: table(5)
        Out[3]: 10.0

        In [4]: table(5.1)
        Out[4]: 10.2

        """
        from interpolation import LinearInterpolation
        table = LinearInterpolation(
                x_index=(2,3,4),
                values=(4,3,8),
                extrapolate=True
            )
        self.response.write(str(table(3)))


__author__ = 'andrew.vasyltsiv'