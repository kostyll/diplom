# -*- coding: utf8 -*-

from google.appengine.ext import db

class Metrix(db.Model):
    mackkeib = db.StringProperty()
    holsted = db.StringProperty()
    jilb = db.StringProperty()
    sloc = db.StringProperty()


class Vulnerability(db.Model):
    vulnerability = db.StringProperty()


class Project(db.Model):
    short = db.StringProperty()
    name = db.StringProperty()
    metrix = db.ReferenceProperty(Metrix, default=None)
    vulnerability = db.ReferenceProperty(Vulnerability, default=None)
    p = db.FloatProperty()


class SourceFile(db.Model):
    project = db.ReferenceProperty(Project)
    name = db.StringProperty()
    source = db.BlobProperty()
    metrix = db.ReferenceProperty(Metrix, default=None)
    vulnerability = db.ReferenceProperty(Vulnerability, default=None)
    p = db.FloatProperty()


__author__ = 'andrew.vasyltsiv'