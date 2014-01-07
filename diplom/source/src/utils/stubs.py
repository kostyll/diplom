# -*- coding: utf8 -*-

from collections import namedtuple
from StringIO import StringIO
from io import BytesIO

FileDescriptor = namedtuple("FileDescriptor", "filename content")

files_opened = {}
old_open = open

def func_open(exists_try):
    def func_open(filename,*args,**kwargs):
        global files_opened
        # print files_opened.keys()
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
        # print "mode",mode
        # print "buffer",buffer
        # print "filename",filename

        if files_opened.has_key(filename):
            if not files_opened[filename].closed:
                files_opened[filename].flush()
                files_opened[filename].close()
            # print "dir ",dir(files_opened[filename])
            # print "!buflist[%s]="%filename,files_opened[filename].buflist
            if hasattr(files_opened[filename],'buflist'):
                if len(files_opened[filename].buflist)>0:
                    files_opened[filename] = buffer(files_opened[filename].buflist[0])
                else:
                    files_opened[filename] = buffer()
            else:
                files_opened[filename] = buffer(files_opened[filename].read())
            return files_opened[filename]
        else:
            if exists_try:
                try:
                    # "try to open %s" % filename
                    files_opened.update({filename:buffer(old_open(filename,'r').read())})
                except Exception,e:
                    print e
                    files_opened.update({filename:buffer()})
            else:
                files_opened.update({filename:buffer()})
        # print 'files_opened',files_opened
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

    f = force_open('stubs.py')
    print "stubs.py:\n",f.read()
    f.close()

    #print files_opened.keys()

    f = force_open('stubs.py','w')
    f.write('asdfsdfsdf')
    f.close()
    print "stubs.py after write:\n",force_open('stubs.py').read()


if __name__ == '__main__':
    main()


__author__ = 'andrew.vasyltsiv'