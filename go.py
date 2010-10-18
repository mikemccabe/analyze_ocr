import sys
from iabook import *
from windowed_iterator import windowed_iterator
import find_pagenos
# import find_header_footer
import make_toc
import json

djvu = True
# djvu = False
pagenos = True
hfs = False

scandata_ns = ''
def main(args):
    doc = ''
    callback = None
    if len(args) == 4:
        (item_id, doc, path, callback) = args
    elif len(args) == 3:
        (item_id, doc, path) = args
    else:
        print len(args)
        print args
        (book_id,) = args
        path = book_id

    book_id = args[0]
    iabook = Book(book_id, doc, path)
    global scandata_ns
    scandata_ns = iabook.get_scandata_ns()
    if djvu:
        pages = iabook.get_pages_as_djvu()
    else:
        pages = iabook.get_pages_as_abbyy()
    pages = filter(pages)
    pages = annotate(pages)
    def clear_page(page):
        page.clear()
    windowed_pages = windowed_iterator(pages, 5, clear_page)
    pages = analyze(windowed_pages)
    toc, qdtoc = make_toc.make_toc(iabook, pages)
    if not make_toc.check_toc(qdtoc):
        qdtoc = []

    # print '\n'.join(str(ti) for ti in toc)
    # print
    # print '\n'.join(str(ti) for ti in qdtoc)
    if callback is not None:
        print '%s(' % callback
    print_one_per_line(qdtoc)
    if callback is not None:
        print ')'
    # consume(pages)


def print_one_per_line(a):
    def printel(el):
        return '%s %s -%s- %s' % (el['tocpage'],
                                  el['pagenum'].rjust(3),
                                  el['label'],
                                  el['title'])
    print '\n'.join(printel(el) for el in a)
    # print '['
    # print ',\n'.join(json.dumps(el) for el in a)
    # # for el in a:
    # #     print json.dumps(el) + ','
    # print ']'



def filter(pages):
    for page in pages:
        # if page.index % 1 == 0:
        #     drawable = page.get_drawable()
        #     page.draw_basics(drawable)
        #     drawable.save()
        if page.scandata.findtext(scandata_ns + 'addToAccessFormats') == 'true':
            yield page


def annotate(pages):
    for page in pages:
        page.info['type'] = page.scandata.findtext(scandata_ns
                                                   + 'pageType').lower()
        number = page.scandata.findtext(scandata_ns + 'pageNumber')
        if number is not None:
            page.info['number'] = number.lower()
        else:
            page.info['number'] = ''

        page.info['bounds'] = page.find_text_bounds()
        if pagenos:
            find_pagenos.annotate_page(page)
        # if hfs:
        #     find_header_footer.annotate_page(page)
        yield page
        page = None


def analyze(windowed_pages):
    for page in windowed_pages:
        if pagenos:
            find_pagenos.guess_best_pageno(page, windowed_pages,
                                           windowed_pages.window)
        # if hfs:
        #     find_header_footer.guess_hf(page, windowed_pages)
        yield page


def consume(pages):
    for page in pages:
        # print page.info
        page = None

if __name__ == '__main__':
    main(sys.argv[1:])
