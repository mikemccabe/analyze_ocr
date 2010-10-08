import re
from lxml import etree
from rnums import rnum_to_int

from tuples import *

ns = '{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'

def guess_best_pageno(pageinfo, pages, window=None):
    """ Select the best candidate pagenumber for the given page,
    with reference to neighboring pages.
    """
    if window is None:
        window = pages.window
    def tally(pageinfo, current_index, sofar, weight):
        for c in pageinfo.info['pageno_candidates']:
            if c.offset >= current_index:
                continue
            if c.offset not in sofar[c.type]:
                sofar[c.type][c.offset] = weight
            else:
                sofar[c.type][c.offset] += weight
    sofar = {'roman':{},'arabic':{}}
    tally(pageinfo, pageinfo.index, sofar, 2)
    for neighbor_info in pages.neighbors(window):
        tally(neighbor_info, pageinfo.index, sofar, 1)

    def thin(obj):
        kys = [k for k in obj]
        for k in kys:
            if obj[k] < 2:
                del obj[k]
    thin(sofar['roman'])
    thin(sofar['arabic'])

    mostsofar = None
    votes = 0
    likelytype = None
    for k in sofar['arabic']:
        if sofar['arabic'][k] > votes:
            votes = sofar['arabic'][k]
            likelytype = 'arabic'
            mostsofar = k
    for k in sofar['roman']:
        if sofar['roman'][k] > votes:
            votes = sofar['roman'][k]
            likelytype = 'roman'
            mostsofar = k

    pageno_guess = None
    if mostsofar:
        pageno_guess = pageinfo.index - int(mostsofar)
        print 'index %s: page guess %s %s' % (pageinfo.index, pageno_guess, likelytype)
        pageinfo.info['pageno_guess'] = pageno_guess

        # if a page coord candidate on *this* page matches, capture it
        for c in pageinfo.info['pageno_candidates']:
            if c.type == likelytype and c.offset == mostsofar:
                # just take first potential coordinate for now
                pageinfo.info['pageno_fmt'] = c.coords[0][0]
                pageinfo.info['pageno_coord'] = c.coords[0][1]
                break

    return pageno_guess

#     print 'roman:  %s' % json.dumps(sofar['roman'])
#     print 'arabic: %s' % json.dumps(sofar['arabic'])

re_roman = re.compile(r'\b[xvi]+\b')
re_arabic = re.compile(r'\b\d+\b')

def annotate_page(page):
    cands = [c for c in pageno_candidates(page, page.page, page.index)]
    page.info['pageno_candidates'] = cands


def pageno_candidates(pageinfo, page, index):
    seen = {}

    # find margin % of top/bottom of text bounding box
    pagebounds = pageinfo.info['bounds']
    page_height = int(page.get('height'))
    margin = .05
    top_margin = pagebounds.t + page_height * margin
    bottom_margin = pagebounds.b - page_height * margin



    # findexpr = './/'+ns+'formatting'
    # for fmt in page.findall(findexpr):

        # # move on if not near page top/bottom
        # line = fmt.getparent()
        # t = int(line.get('t'))
        # b = int(line.get('b'))

        # if t > top_margin and t < bottom_margin:
        #     continue

        # fmt_text = etree.tostring(fmt,
        #                           method='text',
        #                           encoding=unicode).lower();
    for word in pageinfo.get_words():
        fmt_text = word

        # def find_coords(m):
        #     # l t r b
        #     start, end = m.span()
        #     if end >= len(fmt):
        #         end = len(fmt) - 1
        #     return Coord(fmt[start].get('l'), t, fmt[end].get('r'), b)
        def find_coords(m):
            return Coord(1,2,3,4)

        # look for roman numerals
        # fix some common OCR errors
        # XXX RESTORE adjusted_text = (fmt_text.replace('u', 'ii')
        #                  .replace('n', 'ii')
        #                  .replace('l', 'i')
        #                  .replace(r"\'", 'v'))
        adjusted_text = fmt_text

        # collapse space between potential roman numerals
        # XXX RESTORE adjusted_text = re.sub(r'\b([xvi]+)\b +\b([xvi]+)\b', r'\1\1', adjusted_text)
        for m in re_roman.finditer(adjusted_text):
            num_str = m.group()
            if not num_str in seen:

                i = rnum_to_int(num_str)
                if i > index and i != 0:
                    continue
                seen[num_str] = Pageno('roman', num_str, i, index - i,
                                       [(word, find_coords(m))])
                                       # [(fmt, find_coords(m))])
            else:
                seen[num_str].coords.append((word, find_coords(m)))
                # seen[num_str].coords.append((fmt, find_coords(m)))
            yield seen[num_str]

        # look for arabic numerals
        # fix some common OCR errors
        # XXX RESTORE adjusted_text = fmt_text.replace('i', '1').replace('o', '0').replace('s', '5').replace('"', '11')
        # collapse spaces
        # XXX RESTORE adjusted_text = re.sub(r'\b(\d+)\b +\b(\d+)\b', r'\1\1', adjusted_text)
        for m in re_arabic.finditer(adjusted_text):
            num_str = m.group()
            if not num_str in seen:
                i = int(num_str)
                if i > index and i != 0:
                    continue
                seen[num_str] = Pageno('arabic', num_str, i, index - i,
                                       [(word, find_coords(m))])
                                       # [(fmt, find_coords(m))])
            else:
                seen[num_str].coords.append((word, find_coords(m)))
                # seen[num_str].coords.append((fmt, find_coords(m)))
            yield seen[num_str]
