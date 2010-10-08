from difflib import SequenceMatcher, get_close_matches, Match
from extract_sorted import extract_sorted
from rnums import rnum_to_int
from interval import Interval, IntervalSet

from collections import namedtuple


class pagenocand(namedtuple('pagenocand', 'numtype val word_index')):
    pass

def make_toc(iabook, pages):
    contentscount = iabook.get_contents_count()
    contentscount = 0
    skipfirst = 0
    n = 13
    n_optimistic = 1
    tcs = []
    thresh = 5 # if some tc page goes above this score, then...
    starttoc = 0 # starttoc is set to skip prev pages.
    for page in pages:
        if (len(page.info['number']) == 0
            and 'pageno_guess' in page.info):
            page.info['number'] = str(page.info['pageno_guess'])

        # if 'pageno_guess' in page.info:
        #     print 'yah'
        #     page.info['number'] = str(page.info['pageno_guess'])

        # skip on if we're waiting for a contents page
        if (len(tcs) == 0
            and contentscount > 0
            and page.info['type'] != 'contents'):
            continue
        if page.index < skipfirst:
            continue
        print "%s: %s %s" % (page.index, page.info['number'],
                             page.info['type'])
        wipetil = 0
        score = 0
        for i, tc in enumerate(tcs):
            if i < starttoc:
                continue
            print 'MATCH WITH TC PAGE %s' % i
            tc.match_page(page)
            if starttoc == 0 and tc.score > thresh:
                starttoc = i
        # if contentscount is
        # 0: build contents pages for first n pages - need to remember to score all
        # 2+: build contents pages exactly for designated pages
        # 1: skip pages before 1rst contents page, build n_optimistic pages, remember to score later pages
        if ((contentscount == 0 and len(tcs) < n)
            or (contentscount == 1 and len(tcs) < n_optimistic)
            or (contentscount > 1 and len(tcs) < contentscount
                and page.info['type'] == 'contents')):
                tcs.append(TocCandidate(page))
    for tc in tcs:
        tc.printme()

class RangeMatch(object):
    # intervals, in the intervalset, point here
    def __init__(self, tc, page, match):
        self.page = page
        self.tc = tc # Give all pages words... and make toccandidate a page, to get round this?
        self.score = match.size
        self.pageindex = page.index
        self.pageno = page.info['number']
        self.nearno = -1 # index of nearby page_cand
        self.match = match
        self.notes = ''
    def __repr__(self):
        words = ' '.join(self.tc.words[i] for i in range(self.match.b, self.match.b + self.match.size)).encode('utf-8')
        return "%s\tscore %s pageno %s\t%s pagenos %s notes %s" % (self.match,
                                                         self.score,
                                                         self.pageno,
                                                         words,
                                                         self.pagenos,
                                                         self.notes)


class RangeSet(object):
    def __init__(self):
        self.s = []
    def add(r):
        self.s.append(r)
    def overlaps(r):
        for rs in s:
            if ((rs.match.b < r.match.b
                 and rs.match.b + rs.match.size >= r.match.b)
                or (rs.match.b >= r.match.b
                    and r.match.b + r.match.size >= rs.match.b)):
                yield rs

class TocCandidate(object):
    def __init__(self, page):
        self.page = page
        self.matcher = SequenceMatcher()
        self.words = [word for word in page.get_words()]
        self.wordhash = {}
        for word in self.words:
            self.wordhash[word] = True
        self.matcher.set_seq2(self.words)
        print '\n'.join('%s:%s' % (i, w) for i, w in enumerate(self.words))
        print 'content len: %s' % len(self.words)
        self.lookaside = {}
        self.pageno_candidates = self.find_pageno_candidates(page)
        self.matches = IntervalSet()
        self.matchinfo = {}
        self.score = 0

    def printme(self):
        # print ' '.join('%s:%s' % (i, w) for i, w in enumerate(self.words))
        # print 'content len: %s' % len(self.words)
        # print "%s %s" % (len(self.matches), self.matches)
        # for ival in self.matches:
        #     info = self.matchinfo[ival]
        #     print "%s %s" % (ival, info)
        pass

    def find_nearnos(self, match):
        # XXX worry later about contained.  for now: just next and prev:
        # note that current next, prev is from *end* of match
        left = None
        right = None
        for right in self.pageno_candidates:

            if match.b + match.size - 1 < right.word_index:
                break;
            left = right
        return left, right


    def add_match(self, page, match):
        print
        print match
        info = RangeMatch(self, page, match)
        print info
        pageno = page.info['number']
        pagenoval = rnum_to_int(pageno)
        if pagenoval == 0 and len(pageno) > 0:
            pagenoval = int(pageno)

        matchint = Interval.between(match.b, match.b + match.size)

        overlaps = [m for m in self.matches
                    if m & matchint]
        # print overlaps

        # if nearnos matches either, mark flag and amp score
        if pageno:
            nearnos = self.find_nearnos(match)
            print "GREPME near is [%s] pagenoval %s" % (nearnos, pagenoval)
            for no in nearnos[1], nearnos[0]:
                if no is not None:
                    print no.val
                    if no.val == pagenoval:
                        info.notes += 'nearno: %s' % pageno
                        print "GREPME MATCH tc %s, %s %s" % (self.page.index, pageno, self.score)
                        self.score += 1
                        break
                    if no.val > pagenoval - 10:
                        self.score += .01
                        break

        print 'GREPME info now %s' % (info)

        # cases: no overlap
        if len(overlaps) == 0:
            self.matchinfo[matchint] = info
            self.matches = self.matches + IntervalSet([matchint])
        else:
            start = match.b
            end = match.b + match.size
            for i in overlaps:
                oinfo = self.matchinfo[i]
                ostart = oinfo.match.b
                oend = oinfo.match.b + oinfo.match.size
                if ostart < start:
                    start = ostart
                if oend > end:
                    end = oend
                info.match = Match(0, start, end - start)
                info.score += oinfo.score
                info.pageno = oinfo.pageno
                info.notes = info.notes + ' ' + info.notes
                # for opageno in oinfo.pagenos:
                #     opagecount = oinfo.pagenos[opageno]
                #     if opageno in info.pagenos:
                #         info.pagenos[opageno] += opagecount
                #     else:
                #         info.pagenos[opageno] = opagecount
            self.matches += IntervalSet([matchint])
            (new_i,) = [m for m in self.matches if m & matchint]
            self.matchinfo[new_i] = info

        # else:
        #     for m, info in overlaps:
        #         if info.pageno == page.info


        print "%s %s" % (len(self.matches), self.matches)
        for ival in self.matches:
            info = self.matchinfo[ival]
            print "%s %s" % (ival, info)


        # overlap


        # for existing_match in self.matches:

        # --> get array of matching stuff in matches.
        # existing_matches = IntervalSet([matchint]) &

    def find_pageno_candidates(self, page):
        """ Find the set of all numbers on this page that don't
        e.g. follow 'chapter', then find the largest increasing subset
        of these numbers; we consider it likely that these'll be book
        page numbers """
        # XXX i18m someday
        labels = ('chapter', 'part', 'section', 'book')
        def get_page_cands(page):
            lastword = ''
            for i, word in enumerate(page.get_words()):
                if lastword in labels:
                    lastword = word
                    continue
                r = rnum_to_int(word)
                # print word.encode('utf-8')
                if r != 0:
                    yield pagenocand('0roman', r, i)
                if word.isdigit():
                    val = int(word):
                    if val < 999:
                        # XXX replace above check with book page count
                        # if avail.
                        yield pagenocand('1arabic', int(word), i)
                lastword = word
        def printword(c):
            ar, val, loc = c
            print "%s %s - %s" % (ar, val, self.words[loc])
        page_cands = [c for c in get_page_cands(page)]
        #
        print 'cands'
        for c in page_cands:
            printword(c)
        print page_cands
        #
        result = page_cands
        # if len(page_cands) != 0:
        #     result = extract_sorted(page_cands)
        print 'page_nums'
        for c in result:
            printword(c)
        return result

    def match_page(self, page):
        words = [word for word in page.get_words()]
        print ' '.join(words).encode('utf-8')
        for i, word in enumerate(words):
            words[i] = self.reify(word)
        self.matcher.set_seq1(words)
        page_matches = self.matcher.get_matching_blocks()
        page_matches.pop() # lose trailing non-match
        def smallmatch(m):
            smallwords = ('a', 'and', 'the', 'i', 'in', 'to', 'of', 'with')
            smallphrases = (('in', 'the'))
            if m.size > 2:
                return False
            if m.size == 1:
                word = self.words[m.b]
                if word in smallwords:
                    return True
            if m.size == 2:
                word = self.words[m.b]
                word2 = self.words[m.b + 1]
                if (word, word2) in smallphrases:
                    return True
            if len(word) < 3:
                return True
            return False
        page_matches = [m for m in page_matches if not smallmatch(m)]
        for page_match in page_matches:
            # print "%s %s" % (page_match,
            #                  self.decode_match(page_match).encode('utf-8'))
            self.add_match(page, page_match)
    def decode_match(self, match):
        return ' '.join(self.words[i] for i in range(match.b, match.b + match.size))
    def reify(self, word):
        if word in self.wordhash:
            return word
        if word in self.lookaside:
            return self.lookaside[word]
        candidates = get_close_matches(word, self.words, n=1, cutoff=.9)
        if len(candidates) > 0:
            candidate = candidates[0]
            print "%s --> %s" % (word.encode('utf-8'), candidate.encode('utf-8'))
            self.lookaside[word] = candidate
            return candidate
        self.lookaside[word] = word
        return word

