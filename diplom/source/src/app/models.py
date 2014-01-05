# -*- coding: utf8 -*-

from google.appengine.ext import db

class Metrix(db.Model):
    mackkeib = db.StringProperty()
    holsted = db.StringProperty()
    jilb = db.StringProperty()


class Vulnerability(db.Model):
    vulnerability = db.StringProperty()


class Project(db.Model):
    name = db.StringProperty()
    metrix = db.ReferenceProperty(Metrix, default=None)
    vulnerability = db.ReferenceProperty(Vulnerability, default=None)


class SourceFile(db.Model):
    project = db.ReferenceProperty(Project)
    name = db.StringProperty()
    source = db.BlobProperty()
    metrix = db.ReferenceProperty(Metrix, default=None)
    vulnerability = db.ReferenceProperty(Vulnerability, default=None)


__author__ = 'andrew.vasyltsiv'