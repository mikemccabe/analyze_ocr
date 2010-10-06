import re
from lxml import etree
from diff_match_patch import diff_match_patch


ns = '{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'


# Header/Footer detection parameters

# Weights to assign to potential headers / footers.
# len(weights) should be even.
weights = (1.0, .75,
           .75, 1.0)
# weights = (1.0, .75, .5,
#            .5, .75, 1.0)

# allow potential headers/footers with this length difference
max_length_difference = 4

dmp = diff_match_patch()
dmp.Match_Distance = 2 # number of prepended characters allowed before match
dmp.Match_Threshold = .5 # 0 to 1 ... higher => more fanciful matches,
                         # slower execution.

# minimum match score for a line to be considered a header or footer.
min_score = .9



def annotate_page(page):
    cands = [c for c in hf_candidates(page)]
    page.info['hf_candidates'] = cands


def hf_candidates(page):
    result = []
    hfwin = len(weights) / 2
    lines = [line for line in page.page.findall('.//LINE')]
    for i in range(hfwin) + range(-hfwin, 0):
        if abs(i) < len(lines):
            result.append((lines[i], simplify_line_text(lines[i])))
        else:
            result.append(None)
    return result


# def hf_candidates(page):
#     result = []
#     lines = [line for line in page.page.findall('.//'+ns+'line')]
#     hfwin = 5
#     for i in range(hfwin) + range(-hfwin, 0):
#         if abs(i) < len(lines):
#             result.append((lines[i], simplify_line_text(lines[i])))
#         else:
#             result.append(None)
#     return result

def simplify_line_text(line):
    text = etree.tostring(line,
                          method='text',
                          encoding=unicode).lower();
    # collape numbers (roman too) to '@' so headers will be more
    # similar from page to page
    return re.sub(r'[ivx\d]', r'@', text)
    text = re.sub(r'\s+', r' ', text)

def guess_hf(pageinfo, pages, window=None):
    if window is None:
        window = pages.window

    result = []
    pageinfo.info['hf_guesses'] = result
    hf_candidates = pageinfo.info['hf_candidates']
    if 'pageno_fmt' in pageinfo.info:
        pageno_fmt = pageinfo.info['pageno_fmt']
        pageno_line = pageno_fmt.getparent()
    else:
        pageno_fmt = None
        pageno_line = None

    for i in range(len(weights)):
        if hf_candidates[i] is None:
            continue
        score = 0
        if hf_candidates[i][0] == pageno_line:
            score = 2
        # if levenshtein(hf_candidates[i][1], 'chapter @') < 5:
        #     score = 2
        for neighbor_info in pages.neighbors(window):
            score += (weights[i]
                      * text_similarity(pageinfo, neighbor_info, i)
                      * geometry_similarity(pageinfo, neighbor_info, i))
            if score > min_score:
                result.append(i)
                # result.append(hf_candidates[i])
                break
        if score < min_score:
            # remove it from the running, so it doesn't slow down later checks
            hf_candidates[i] = None
    # print 'result' + '  '.join(str(hf[1].encode('utf-8')) for hf in result)
    return result

def text_similarity(pageinfo, neighbor_info, i):
    neighbor_candidate = neighbor_info.info['hf_candidates'][i]
    if neighbor_candidate is None:
        return 0
    neighbor_line, neighbor_text = neighbor_candidate
    line, text = pageinfo.info['hf_candidates'][i]
    if abs(len(text) - len(neighbor_text)) > max_length_difference:
        return 0
    matchstart = dmp.match_main(text, neighbor_text, 0)
    if matchstart != -1:
        return 1
    else:
        return 0
    # distance = levenshtein(neighbor_text, text)
    # if distance > maxlen:
    #     return 0
    # return (maxlen - distance) / maxlen

def geometry_similarity(pageinfo, neighbor_info, i):
    return 1
