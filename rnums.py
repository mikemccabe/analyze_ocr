rnums = {
    'i':1, 'ii':2, 'iii':3, 'iv':4, 'v':5,
    'vi':6, 'vii':7, 'viii':8, 'ix':9, 'x':10,
    'xi':11, 'xii':12, 'xiii':13, 'xiv':14, 'xv':15,
    'xvi':16, 'xvii':17, 'xviii':18, 'xix':19, 'xx':10,
    'xxi':21, 'xxii':22, 'xxiii':23, 'xxiv':24, 'xxv':25,
    'xxvi':26, 'xxvii':27, 'xxviii':28, 'xxix':29, 'xxx':30,
    'xxxi': 31, 'xxxii': 32, 'xxxiii': 33, 'xxxiv':34, 'xxxv':35,
    'xxxvi':36, 'xxxvii':37, 'xxxviii':38, 'xxxix':39, 'xl':40,
    'xli':41, 'xlii':42, 'xliii':43, 'xliv':44, 'xlv':45,
    'xlvi':46, 'xlvii':47, 'xlviii':48, 'xlix':49, 'l':50,
    'li':51, 'lii':52, 'liii':53, 'liv':54, 'lv':55,
    'lvi':56, 'lvii':57, 'lviii':58, 'lix':59, 'lx':60,
    'lxi':61, 'lxii':62, 'lxiii':63, 'lxiv':64, 'lxv':65,
    'lxvi':66, 'lxvii':67, 'lxviii':68, 'lxix':69, 'lxx':70,
    # lxx lccc
    }
def rnum_to_int(r):
    r = r.lower()
    if r in rnums:
        return rnums[r]
    return 0

