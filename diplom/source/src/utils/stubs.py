# -*- coding: utf8 -*-

from collections import namedtuple
from StringIO import StringIO
from io import BytesIO

FileDescriptor = namedtuple("FileDescriptor", "filename content")

files_opened = {}

def func_open(exists_try):
    def func_open(filename,*args,**kwargs):
        global files_opened
        buffer = StringIO
        if len(args) > 0:
            mode = args[0]
        else:
            mode = 'r'
        if 'r' in mode.lower():
            pass
        if 'w' in mode.lower():
            pass

        if 'b' in mode.lower():
            buffer = BytesIO

        if files_opened.has_key(filename):
            if not files_opened[filename].closed:
                files_opened[filename].flush()
                files_opened[filename].close()
            #print "!buflist[%s]="%filename,files_opened[filename].buflist
            if len(files_opened[filename].buflist)>0:
                files_opened[filename] = buffer(files_opened[filename].buflist[0])
            else:
                files_opened[filename] = buffer()
            return files_opened[filename]
        else:
            if exists_try:
                try:
                    files_opened.update({filename:open(filename,mode)})
                except:
                    files_opened.update({filename:buffer()})
            else:
                files_opened.update({filename:buffer()})
        return files_opened[filename]

    return func_open


open = func_open(False)   
force_open = func_open(True)



def main():
    testfile_content = """asdfsdfqwerwkefqweruwygfweirweiqrwruqwasdasd

    asdfsdfqwerwkefqweruwygfweirweiqrwruqwasdasdd
    asdfsdfqwerwkefqweruwygfweirweiqrwruqwasdasddsd
    asdfsdfqwerwkefqweruwygfweirweiqrwruqwasdasddsd
    asdfsdfqwerwkefqweruwygfweirweiqrwruqwasdasddsde
    rt
    er
    tyt5555555555555"""

    fw = open('file1','w')
    fw.write(testfile_content)
    fw.close()

    fr = open('file1','r')
    content = fr.read()
    print "testfile_content = read content ? - %s " % (testfile_content == content)
    print content

if __name__ == '__main__':
    main()


__author__ = 'andrew.vasyltsiv'