import os
from StringIO import StringIO
from lxml import etree
import zipfile
import gzip
import re


class Book(object):
    def __init__(self, book_id, doc, book_path):
        self.book_id = book_id
        self.doc = doc
        if len(self.doc) == 0:
            self.doc = self.book_id
        self.book_path = book_path
        if not os.path.exists(book_path):
            raise Exception('Can\'t find book path "' + book_path + '"')
        self.scandata = self.get_scandata()
        self.scandata_ns = self.get_scandata_ns()


    def get_scandata_ns(self):
        scandata = self.get_scandata()
        bookData = scandata.find('bookData')
        if bookData is None:
            return '{http://archive.org/scribe/xml}'
        else:
            return ''


    def get_scandata(self):
        result = None
        for f in (os.path.join(self.book_path, self.doc + '_scandata.xml'),
                  os.path.join(self.book_path, 'scandata.xml')):
            if os.path.exists(f):
                result = etree.parse(f)
                break
        if result is None:
            f = os.path.join(self.book_path, 'scandata.zip')
            if not os.path.exists(f):
                raise Exception('No scandata found')
            z = zipfile.ZipFile(f, 'r')
            scandata_str = z.read('scandata.xml')
            z.close()
            result = etree.parse(StringIO(scandata_str))
        return result


    def get_abbyy(self):
        abbyy_gz = os.path.join(self.book_path, self.doc + '_abbyy.gz')
        if os.path.exists(abbyy_gz):
            return gzip.open(abbyy_gz, 'rb')
        abbyy_zip = os.path.join(self.book_path, self.doc + '_abbyy.zip')
        if os.path.exists(abbyy_zip):
            return os.popen('unzip -p ' + abbyy_zip + ' ' + self.doc + '_abbyy.xml')
            # z = zipfile.ZipFile(abbyy_zip, 'r')
            # return z.open(self.doc + '_abbyy.xml') # only in 2.6... speed is same
        abbyy_xml = os.path.join(self.book_path, self.doc + '_abbyy.xml')
        if os.path.exists(abbyy_xml):
            return open(abbyy_xml, 'r')
        raise 'No abbyy file found'


    def get_djvu_xml(self):
        djvu_xml = os.path.join(self.book_path, self.doc + '_djvu.xml')
        if os.path.exists(djvu_xml):
            return open(djvu_xml, 'r')
        raise 'No djvu.xml file found'


    def get_scandata_pages_djvu(self):
        for page in self.scandata.findall('.//' + self.scandata_ns + 'page'):
            add = page.find(self.scandata_ns + 'addToAccessFormats')
            if add is not None and add.text == 'true':
                yield page


    def get_scandata_pages(self):
        for page in self.scandata.findall('.//' + self.scandata_ns + 'page'):
            yield page


    def get_leafcount(self):
        leafcount = self.scandata.findtext('%sbookData/%sleafCount'
                                           % (self.scandata_ns,
                                              self.scandata_ns))
        if leafcount is not None:
            leafcount = int(leafcount)
        return leafcount

def nsify(tagpath, ns) :
    return '/'.join(ns + tag for tag in tagpath)
