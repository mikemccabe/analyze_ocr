import sys
import os
from StringIO import StringIO
from lxml import etree
import zipfile
import gzip
import re
from collections import namedtuple

ns="{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}"
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


    def get_contents_count(self):
        return len([True for e
                    in self.scandata.findall('.//%spageType' % (self.scandata_ns))
                    if e.text.lower() == 'contents'])


    def get_pages_as_abbyy(self):
        abbyy = self.get_abbyy()
        scandata_iter = self.get_scandata_pages()
        for i, (event, page) in enumerate(etree.iterparse(abbyy,
                                                          tag=ns+'page')):
            yield abbyypage(i, page, scandata_iter.next())

    def get_pages_as_djvu(self):
        djvu = self.get_djvu_xml()
        scandata_iter = self.get_scandata_pages_djvu()
        for i, (event, page) in enumerate(etree.iterparse(djvu,
                                                          tag='OBJECT')):
            yield djvupage(i, page, scandata_iter.next())


box = namedtuple('box', 'l t r b')


# class scandata_page:
#     def __init__(self, sd):
#         self.sd = sd
#     def pageno():


class abspage(object):
    def __init__(self, i, page, page_scandata):
        self.index = i
        self.page = page
        self.scandata = page_scandata
        self.info = {}


class djvupage(abspage):
    def get_words(self):
        lines = self.page.findall('.//LINE')
        for line in lines:
            words = line.findall('.//WORD')
            for word in words:
                # sometimes 4 coords, sometimes 5
                l, b, r, t = word.get('coords').split(',')[:4]
                # if (int(b) - int(t)) < 50:
                #     continue
                text = word.text
                # l b r t
                text = re.sub(r'[\s.:,\(\)\/;!\'\"\-]', '', text)
                text.strip()
                if len(text) > 0:
                    yield text.lower().encode('ascii', 'ignore')
    def find_text_bounds(self):
        l = t = sys.maxint
        r = b = 0
        textfound = False
        lines = self.page.findall('.//LINE')
        for line in lines:
            words = line.findall('.//WORD')
            if len(words) == 0:
                continue
            textfound = True
            for word in (words[0], words[-1]):
                intcoords = [int(w) for w in word.get('coords').split(',')]
                bl, bb, br, bt = intcoords[:4]
                if bl < l: l = bl
                if bt < t: t = bt
                if br > r: r = br
                if bb > b: b = bb
        if not textfound:
            l = 0
            t = 0
            r = int(self.page.get('width'))
            b = int(self.page.get('height'))
        return box(l, t, r, b)
    def clear(self):
        self.page.clear()
        self.page = None


class abbyypage(abspage):
    def get_words(self):
        findexpr = './/'+ns+'charParams'
        chars = []
        for char in self.page.findall(findexpr):
            if char.get('wordStart') == 'true':
                if len(chars) > 0:
                    # xxx not sure if necessary
                    t = ''.join(c.text for c in chars).lower().encode('ascii', 'ignore')
                    t.strip()
                    if len(t) > 0:
                        yield t
                    chars = []
                text = re.sub(r'[\s.:,\(\)\/;!\'\"\-]', '', text)
            if char.text not in (' ', '.', '"', ';', '/', '\'', ':'):
                chars.append(char)
            else:
                pass
        if len(chars) > 0:
            # xxx not sure if necessary
            t = ''.join(c.text for c in chars).lower().encode('ascii', 'ignore')
            t.strip()
            if len(t) > 0:
                yield t
            chars = []
    def find_text_bounds(self):
        l = t = sys.maxint
        r = b = 0
        textfound = False
        for block in self.page.findall('.//'+ns+'block'):
            if block.get('blockType') != 'Text':
                continue
            textfound = True
            bl = int(block.get('l'))
            if bl < l: l = bl

            bt = int(block.get('t'))
            if bt < t: t = bt

            br = int(block.get('r'))
            if br > r: r = br

            bb = int(block.get('b'))
            if bb > b: b = bb

        if not textfound:
            l = 0
            t = 0
            r = int(self.page.get('width'))
            b = int(self.page.get('height'))
        return box(l, t, r, b)
    def clear(self):
        self.page.clear()
        self.page = None


def nsify(tagpath, ns) :
    return '/'.join(ns + tag for tag in tagpath)
