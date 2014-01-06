# -*- coding: utf8 -*-

from collections import namedtuple
from functools import reduce
Source = namedtuple("Source", "project file_name file_source file_db_item holsted mackkeib jilb sloc vulns")

class SourceFilesFormatError(Exception):
    pass

from app.models import (
        Project,
        SourceFile,
        Metrix,
        Vulnerability
    )

from vertix.metrix import (
        get_holsted,
        get_mackkeib,
        get_jilb,
        get_sloc
    )

from vertix.vulns import (
        get_vulns_count
    )

from vertix import get_ast_from_text

class SourceProcessor():
    def __init__(self, project_files, project_name):
        print project_name
        if not isinstance(project_files, dict):
            raise TypeError ("project_files have to be dict")
        if not isinstance(project_name, str):
            raise TypeError("project_name must to be str")
        try:
            if project_files['error'] == False:
                if isinstance (project_files['project'], (list)):
                    # list of files
                    self.project_files = project_files['project']
                    self.project_name = project_name
                    self.project = Project.get_or_insert('name='+self.project_name)
                    self.project.name = self.project_name
                    self.files = []
                    self.process_sources()
                    self.project.put()
                else:
                    raise SourceFilesFormatError
            else:
                raise SourceFilesFormatError
        except AttributeError:
            raise SourceFilesFormatError

    def process_sources(self):
        for file_name,file_source in self.project_files:
            ast = None#get_ast_from_text(file_source)
            holsted = (get_holsted(file_source,ast))
            mackkeib = (get_mackkeib(file_source,ast))
            jilb = (get_jilb(file_source,ast))
            sloc = (get_sloc(file_source,ast))
            vulns = (get_vulns_count(file_source,ast))

            metrix = Metrix(
                            holsted = str(holsted),
                            mackkeib = str(mackkeib),
                            jilb = str(get_jilb),
                            sloc = str(sloc)
                        )
            metrix.put()
            vulnerability = Vulnerability(
                                    vulnerability = str(vulns)
                                )
            vulnerability.put()


            source = Source(
                    project = self.project,
                    file_name = file_name,
                    file_source = file_source,
                    file_db_item = SourceFile(
                            project = self.project,
                            name = file_name,
                            source = file_source,
                            metrix = metrix,
                            vulnerability = vulnerability
                        ),
                    holsted = holsted,
                    mackkeib = mackkeib,
                    jilb = jilb,
                    sloc = sloc,
                    vulns = vulns
                )
            source.file_db_item.put()
            self.files.append(source)

        # sloc, holsted, mackkeib, jilb, vulns = reduce(

        #     )

        sloc = reduce(lambda x,y: x+y, map(lambda x: x.sloc, self.files))
        holsted = reduce(lambda x,y: x+y, map(lambda x: x.holsted, self.files))
        mackkeib = reduce(lambda x,y: x+y, map(lambda x: x.mackkeib, self.files))
        jilb = reduce(lambda x,y: x+y, map(lambda x: x.jilb, self.files))
        vulns = reduce(lambda x,y: x+y, map(lambda x: x.vulns, self.files))

        metrix = Metrix(
                sloc = str(sloc),
                holsted = str(holsted),
                mackkeib = str(mackkeib),
                jilb = str(jilb)
            )
        metrix.put()
        self.project.metrix = metrix
        vulnerability = Vulnerability(
                vulnerability = str(vulns)
            )
        vulnerability.put()
        self.project.vulnerability = vulnerability


__author__ = 'andrew.vasyltsiv'