import sys
import os
from StringIO import StringIO
from lxml import etree
import zipfile
import gzip
import re
from collections import namedtuple

import Image
import ImageDraw
# import ImageFont
# import color
# from color import color as c


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
        self.images_type = 'unknown'
        if os.path.exists(os.path.join(book_path, self.doc + '_jp2.zip')):
            self.images_type = 'jp2.zip'
        elif os.path.exists(os.path.join(book_path, self.doc + '_tif.zip')):
            self.images_type = 'tif.zip'
        elif os.path.exists(os.path.join(book_path, self.doc + '_jp2.tar')):
            self.images_type = 'jp2.tar'


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
            yield abbyypage(i, self, page, scandata_iter.next())


    def get_pages_as_djvu(self):
        djvu = self.get_djvu_xml()
        scandata_iter = self.get_scandata_pages_djvu()
        for i, (event, page) in enumerate(etree.iterparse(djvu,
                                                          tag='OBJECT')):
            yield djvupage(i, self, page, scandata_iter.next())


    # get python string with image data - from .jp2 image or tif in zip
    def get_page_image(self, leafno, requested_size, orig_page_size=None,
                       quality=60,
                       region=None, # ((l,t)(r,b))
                       out_img_type='jpg',
                       kdu_reduce=2):
        doc_basename = os.path.basename(self.doc)
        if self.images_type == 'jp2.zip':
            zipf = os.path.join(self.book_path,
                                self.doc + '_jp2.zip')
            image_path = (doc_basename + '_jp2/' + doc_basename + '_'
                          + leafno.zfill(4) + '.jp2')
            in_img_type = 'jp2'
        elif self.images_type == 'tif.zip':
            zipf  = os.path.join(self.book_path,
                                 self.doc + '_tif.zip')
            image_path = (doc_basename + '_tif/' + doc_basename + '_'
                          + leafno.zfill(4) + '.tif')
            in_img_type = 'tif'
        elif self.images_type == 'jp2.tar':
            # 7z e archive.tar dir/filename.jp2 <---- fast!
            raise 'NYI'
        else:
            return None
        try:
            z = zipfile.ZipFile(zipf, 'r')
            info = z.getinfo(image_path) # for to check it exists
            z.close()
        except KeyError:
            return None
        return image_from_zip(zipf, image_path,
                              requested_size, orig_page_size,
                              quality, region,
                              in_img_type, out_img_type,
                              kdu_reduce)


box = namedtuple('box', 'l t r b')

class abspage(object):
    def __init__(self, i, book, page, page_scandata):
        self.index = i
        self.book = book
        self.page = page
        self.scandata = page_scandata
        self.info = {}
    def get_drawable(self, scale=2, reduce=2, savedir='.'):
        return drawablepage(self, scale, reduce, savedir)


class drawablepage(object):
    def __init__(self, page, scale=2, reduce=2, savedir='.'):
        self.page = page
        self.scale = scale
        self.reduce = reduce
        self.savedir = savedir
        orig_width = int(page.page.get('width'))
        orig_height = int(page.page.get('height'))
        requested_size = (orig_width / scale, orig_height / scale)
        image = Image.new('RGB', requested_size)

        self.leafnum = page.scandata.get('leafNum')
        image_str = page.book.get_page_image(self.leafnum, requested_size,
                                        out_img_type='ppm',
                                        kdu_reduce=reduce)
        page_image = None
        if image_str is not None:
            page_image = Image.open(StringIO(image_str))
            if requested_size != page_image.size:
                page_image = page_image.resize(requested_size)
            try:
                image = Image.blend(image, page_image, .3)
            except ValueError:
                raise 'blending - images didn\'t match'
        self.image = image
        self.draw = ImageDraw.Draw(image)
    def drawbox(self, box, width=1): # xxx fill=
        self.draw.line([(box.l, box.t), (box.r, box.t),
                   (box.r, box.b), (box.l, box.b), (box.l, box.t)],
                       width=width) # xxx fill=color
    def save(self):
        filename = 'img%s.png' % self.page.scandata.get('leafNum').zfill(3)
        # self.image.save('%s/%s' % (self.savedir, filename))
        self.image.save(os.path.join(self.savedir, filename))
    def clear(self):
        self.image.clear()
        self.draw.clear()



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



def get_kdu_region_string(img_size, region):
    if region is not None and img_size is None:
        raise 'need orig image size to support region request'
    if region is None or img_size is None:
        return '{0.0,0.0},{1.0,1.0}'
    w, h = img_size
    w = float(w)
    h = float(h)
    (l, t), (r, b) = region
    result = ('{' + str(t/h) + ',' + str(l/w) + '},' +
              '{' + str((b-t)/h) + ',' + str((r-l)/w) + '}')
    return result

if not os.path.exists('/tmp/stdout.ppm'):
    os.symlink('/dev/stdout', '/tmp/stdout.ppm')
if not os.path.exists('/tmp/stdout.bmp'):
    os.symlink('/dev/stdout', '/tmp/stdout.bmp')

# get python string with image data - from .jp2 image in zip
def image_from_zip(zipf, image_path,
                   requested_size, orig_page_size,
                   quality, region,
                   in_img_type, out_img_type,
                   kdu_reduce):
    if not os.path.exists(zipf):
        raise Exception('Zipfile missing')

    width, height = requested_size
    scale = ' | pnmscale -quiet -xysize ' + str(width) + ' ' + str(height)
#     scale = ' | pamscale -quiet -xyfit ' + str(width) + ' ' + str(height)
    if out_img_type == 'jpg':
        cvt_to_out = ' | pnmtojpeg -quiet -quality ' + str(quality)
    elif out_img_type == 'ppm':
        cvt_to_out = ' | ppmtoppm -quiet'
    else:
        raise Exception('unrecognized out img type')
    if in_img_type == 'jp2':
        kdu_region = get_kdu_region_string(orig_page_size, region)
        output = os.popen('unzip -p ' + zipf + ' ' + image_path
                        + ' | kdu_expand -region "' + kdu_region + '"'
                        +   ' -reduce ' + str(kdu_reduce)
                        +   ' -no_seek -i /dev/stdin -o /tmp/stdout.bmp'
                        + ' | bmptopnm -quiet '
                        + scale
                        + cvt_to_out)
    elif in_img_type == 'tif':
        crop = ''
        if region is not None:
            (l, t), (r, b) = region
            l = str(l); t = str(t); r = str(r); b = str(b)
            crop = (' | pamcut -left=' + l + ' -top=' + t
                    + ' -right=' + r + ' -bottom=' + b)

        import tempfile
        t_handle, t_path = tempfile.mkstemp()
        output = os.popen('unzip -p ' + zipf + ' ' + image_path
                        + ' > ' + t_path)
        output.read()
        output = os.popen('tifftopnm -quiet ' + t_path
                        + crop
                        + scale
                        + cvt_to_out)

    else:
        raise Exception('unrecognized in img type')
    return output.read()
