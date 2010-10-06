from difflib import SequenceMatcher, get_close_matches
from extract_sorted import extract_sorted
from rnums import rnum_to_int



def make_toc(pages):
    tc = None
    matchups = 0
    for page in pages:
        print "%s: %s %s" % (page.index, page.info['number'],
                             page.info['type'])
        if page.info['type'] == 'contents' and tc is None:
            tc = TocCandidate(page)

        elif tc is not None:
            matchups += tc.match_page(page)
    print matchups


# XXX i18m someday
labels = ('chapter', 'part', 'section', 'book')
def get_page_cands(page):
    lastword = ''
    for i, word in enumerate(page.get_words()):
        # if lastword in labels:
        #     lastword = word
        #     continue
        r = rnum_to_int(word)
        print word.encode('utf-8')
        # if r != 0:
        #     yield ('0roman', r, i)
        if word.isdigit():
            yield ('1arabic', int(word), i)
        lastword = word

class TocCandidate(object):
    def __init__(self, page):
        self.page = page
        self.matcher = SequenceMatcher()
        self.matches = []
        self.words = [word for word in page.get_words()]
        self.wordhash = {}
        for word in self.words:
            self.wordhash[word] = True
        self.matcher.set_seq2(self.words)
        print 'content len: %s' % len(self.words)
        self.lookaside = {}
        self.allwords = [word for word in page.get_words()]
        def printword(c):
            ar, val, loc = c
            print "%s %s - %s" % (ar, val, self.allwords[loc])
        page_cands = [c for c in get_page_cands(page)]
        # print page_cands
        # print 'cands'
        # for c in page_cands:
        #     printword(c)
        # print page_cands
        if len(page_cands) != 0:
            self.page_cands = extract_sorted(page_cands)
        # print 'page_nums'
        # if len(page_nums) != 0:
        #     for c in page_nums:
        #         printword(c)
    def add_match(self, page, match):
        pass

    def match_page(self, page):
        words = [word for word in page.get_words()]
        for i, word in enumerate(words):
            words[i] = self.reify(word)
        self.matcher.set_seq1(words)
        matches = self.matcher.get_matching_blocks()
        matches.pop() # lose trailing non-match
        # print matches[-1]
        # matches = matches[0:-1] # skip trailing non-match
        def smallmatch(m):
            smallwords = ('a', 'and', 'the', 'i', 'to', 'of')
            if m.size != 1:
                return False
            word = self.words[m.b]
            if word in smallwords:
                return True
            if len(word) < 3:
                return True
            return False
        matches = [m for m in matches if not smallmatch(m)]
        for match in matches:
            print match
            print self.decode_match(match).encode('utf-8') + ' '
            self.add_match(page, match)
        return len(matches)
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
            print "%s --> %s" % (word, candidate)
            self.lookaside[word] = candidate
            return candidate
        self.lookaside[word] = word
        return word

