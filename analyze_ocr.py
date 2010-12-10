import sys
from iabook import *
from windowed_iterator import windowed_iterator
import find_pagenos
# import find_header_footer
import make_toc
import json

opts = None

djvu = True
# djvu = False
pagenos = False
hfs = False

scandata_ns = ''
def main(argv):
    import optparse
    parser = optparse.OptionParser(usage='usage: %prog [options]',
                                   version='%prog 0.1',
                                   description='make tocs')
    parser.add_option('--human',
                      action='store_true',
                      default=False,
                      help='print some human-readable stuff')
    global opts
    opts, args = parser.parse_args(argv)

    doc = ''
    callback = None
    if len(args) == 4:
        (item_id, doc, path, callback) = args
    elif len(args) == 3:
        (item_id, doc, path) = args
    else:
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
    toc_result = make_toc.make_toc(iabook, pages)

    toc_result['contents_leafnos'] = iabook.get_contents_indices()

    toc_result['readable'] = print_readable(toc_result['qdtoc'])

    if opts.human:
        for r in ('readable', 'comments', 'isok'):
            print r + ':'
            print toc_result[r]
            print
    else:
        if callback is not None:
            print '%s(' % callback
            print json.dumps(toc_result)
        if callback is not None:
            print ')'
        else:
            print json.dumps(toc_result, indent=4)


    # consume(pages)


def print_readable(a):
    maxllen = 0
    maxtlen = 0
    for el in a:
        if len(el['title']) > maxtlen:
            maxtlen = len(el['title'])
        if len(el['label']) > maxllen:
            maxllen = len(el['label'])
    
    def printel(el):
        return '%s  %s  %s %s' % (el['tocpage'],
                                  el['label'].ljust(maxllen + 3),
                                  el['title'].ljust(maxtlen + 3),
                                  el['pagenum'].rjust(3))
    return '\n'.join(printel(el) for el in a)


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
            # use guess if number is not supplied
            if (len(page.info['number']) == 0
                and 'pageno_guess' in page.info):
                page.info['number'] = str(page.info['pageno_guess'])

        # if hfs:
        #     find_header_footer.guess_hf(page, windowed_pages)
        yield page


def consume(pages):
    for page in pages:
        # print page.info
        page = None

if __name__ == '__main__':
    main(sys.argv[1:])
