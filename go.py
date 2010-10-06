import sys
from iabook import *
from windowed_iterator import windowed_iterator
import find_pagenos
import find_header_footer
import make_toc

djvu = True
pagenos = False
hfs = False

scandata_ns = ''
def main(args):
    book_id = args[0]
    iabook = Book(book_id, '', book_id)
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
    toc = make_toc.make_toc(pages)
    # consume(pages)


def filter(pages):
    for page in pages:
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
        if hfs:
            find_header_footer.annotate_page(page)
        yield page
        page = None


def analyze(windowed_pages):
    for page in windowed_pages:
        if pagenos:
            find_pagenos.guess_best_pageno(page, windowed_pages,
                                           windowed_pages.window)
        if hfs:
            find_header_footer.guess_hf(page, windowed_pages)
        yield page


def consume(pages):
    for page in pages:
        # print page.info
        page = None


if __name__ == '__main__':
    main(sys.argv[1:])


