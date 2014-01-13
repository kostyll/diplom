# -*- coding: utf8 -*-

from collections import namedtuple
from StringIO import StringIO
from md5 import md5
import re
from functools import reduce
from interpolation import LinearInterpolation
Source = namedtuple("Source", "project file_name file_source file_db_item holsted mackkeib jilb sloc vulns potential p")

class SourceFilesFormatError(Exception):
    pass

class SourceFileFormatError(SourceFilesFormatError):
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

def remove_Directives(source):
    source = re.sub(r"/\*([^*])+.+[^/]/", "", source)
    
    source = re.sub(r"/\*((?<=\*)[^/]+)/", "", source)
    file = StringIO(source)
    result = []
    for line in file.readlines():
        if line.lstrip(' ').startswith('#'):
            continue
        if line.lstrip(' ').startswith('//'):
            continue
            #line = "//"+line
        if line.find('//')>0:
            line = line.rpartition('//')[0]
        result.append(line)
    return '\n'.join(result)


class SourceProcessor():
    def __init__(self, project_files, project_name):
        print project_name
        if not isinstance(project_files, dict):
            raise TypeError ("project_files have to be dict")
        if not isinstance(project_name, str):
            raise TypeError("project_name must to be str")
        # try:
        if project_files['error'] == False:
            if isinstance (project_files['project'], (list)):
                # list of files
                self.project_files = project_files['project']
                self.project_name = project_name
                self.project = Project.get_or_insert('name='+self.project_name)
                self.project.name = self.project_name
                self.project.short = md5(project_name).hexdigest()
                self.init_sources_for_extrapolation()
                self.files = []
                self.process_sources()
                self.project.put()
            else:
                raise SourceFilesFormatError
        else:
            raise SourceFilesFormatError
        # except Exception, e:
        #     print e
        #     raise SourceFilesFormatError

    @staticmethod
    def calc_potential(v,GZ,Rup,vulns):
        if vulns == 0:
            return float((Rup*GZ)/float(v))
        else:
            return float((vulns*Rup*GZ)/float(v))

    def init_sources_for_extrapolation(self):
        sources = SourceFile.all()
        tab = []
        tab_x = []
        tab_f = []
        for source in sources:
            if source.vulnerability is not None and \
                source.potential is not None and \
                source.p is not None:
                if int(source.vulnerability.vulnerability) >0 :
                    tab.append((source.potential,source.p))
        for i, item in enumerate(tab):
            if tab[i-1] == tab[i]:
                tab.pop(i)
        tab.sort()
        tab = tab
        self.tab_x = map(lambda x: x[0], tab)
        self.tab_f = map(lambda x: x[1], tab)


    @staticmethod
    def calc_p(potential):
        if len(self.tab_x) < 2:
            return 0.5
        try:
            table = LinearInterpolation(
                x_index = tuple(self.tab_x),
                values = tuple(self.tab_f),
                extrapolate=True
                )
            return float(table(potential))
        except:
            return 0.5


    def process_sources(self):

        splitted_source = ""

        for file_name,file_source in self.project_files:

            ast_source = remove_Directives(file_source)

            print "@file_source[%s]"%file_name #,file_source
            try:
                # ast = get_ast_from_text(file_source)
                ast = None
            except Exception, e:
                print e
                debuglines= 8
                line = int(str(e).split(':')[1])
                for i in range(debuglines):
                    try:
                        print "INFO file[%s] line[%s]: %s" % (file_name,line+i-debuglines/2+1,file_source.split('\n')[line+i-debuglines/2])
                    except:
                        pass
                ast = None
            if ast is not None:
                #ast.show()
                # print ast.ext
                pass

            holsted, mackkeib,jilb, sloc = (
                function(file_source,ast) for function in (
                    get_holsted,
                    get_mackkeib,
                    get_jilb,
                    get_sloc
                )
            )

            #BUF to fix
            if holsted != (-1,-1,-1):
                splitted_source += "\n"+file_source
            
            vulns = get_vulns_count(file_source,ast)
        
            metrix = Metrix(
                            holsted = str(holsted),
                            mackkeib = str(mackkeib),
                            jilb = str(jilb),
                            sloc = str(sloc)
                        )
            metrix.put()
            vulnerability = Vulnerability(
                                    vulnerability = str(vulns)
                                )
            vulnerability.put()

            potential = self.calc_potential(
                                    holsted[0],
                                    mackkeib,
                                    jilb,
                                    vulns
                                )
            p = self.calc_p(potential)
            source = Source(
                    project = self.project,
                    file_name = file_name,
                    file_source = file_source,
                    file_db_item = SourceFile(
                            project = self.project,
                            name = file_name,
                            source = file_source,
                            metrix = metrix,
                            vulnerability = vulnerability,
                            potential = potential,
                            p = p
                        ),
                    holsted = holsted,
                    mackkeib = mackkeib,
                    jilb = jilb,
                    sloc = sloc,
                    vulns = vulns,
                    potential = potential,
                    p = p   
                )
            source.file_db_item.put()
            self.files.append(source)

        # sloc, holsted, mackkeib, jilb, vulns = reduce(

        #     )

        sloc = reduce(lambda x,y: x+y, map(lambda x: x.sloc, self.files))

        holsted = get_holsted(splitted_source,None)

        mackkeib = get_mackkeib(splitted_source,None)

        jilb = get_jilb(splitted_source,None)

        vulns = reduce(lambda x,y: (x+y), map(lambda x: x.vulns, self.files))

        potential = reduce(lambda x,y : x if x>y else y, map(lambda x: x.potential, self.files))

        p = reduce(lambda x,y : x if x>y else y, map(lambda x: x.p, self.files))

        self.project.potential = potential
        self.project.p = p

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