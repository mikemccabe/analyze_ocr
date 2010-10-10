from collections import namedtuple

# coords is an array of fmt, coord tuples
class Pageno(namedtuple('Pageno', 'type string value offset coords')):
    pass
    # def clear(self):
    #     for c in self.coords:
    #         c[0].clear()
# class PageInfo(namedtuple('PageInfo', 'page leafno info')):
#     pass
    # def clear(self):
    #     self.page.clear()
#         if 'pageno_candidates' in self.info:
#             for c in self.info['pageno_candidates']:
#                  c.clear()
# #            del self.info['pageno_candidates']
#         if 'pageno_fmt' in self.info:
#             self.info['pageno_fmt'].clear()
# #           del self.info['pageno_fmt']
        # if 'hf_candidates' in self.info:
        #     for i, c in enumerate(self.info['hf_candidates']):
        #          if c is not None:
        #              c[0].clear()
        #          del self.info['hf_candidates'][i]
        #     del self.info['hf_candidates']
        # if 'hf_guesses' in self.info:
        #     print 'here'
        #     for i, c in enumerate(self.info['hf_guesses']):
        #          if c is not None:
        #              c[0].clear()
        #          del self.info['hf_guesses'][i]
        #     del self.info['hf_guesses']

class box(namedtuple('Coord', 'l t r b')):
    pass
    # def findcenter(self):
    #     return (float(self.l) + (float(self.r) - float(self.l)) / 2,
    #             float(self.t) - (float(self.b) - float(self.t)) / 2)

class Word(namedtuple('Word', 'text chars')):
    pass
    # def clear(self):
    #     for char in chars:
    #         char.clear()

class pagenocand(namedtuple('pagenocand', 'numtype val word_index')):
    pass
