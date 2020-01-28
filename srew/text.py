# 14.08.2019
import re
re_word = re.compile(r"(?:(?:\w+|\d+)-\w+|[_\w\d]+)")
# re_word = re.compile(r"(?:(?:\w+|\d+)-\w+|[_\w\d]+|\[id\d+\|.+?\])")


def _rds(text):
    string = ""
    for c in text:
        if c not in string:
            string += c
    return string


class TextParser:
    # space_ignore - игнорировать пробелы в self.prefix и self.words[i][2]
    def __init__(self, text, lower=True):
        self.prefix     = ''            # если перед строкой стоят какое-то символы Not (0-9, А-Я, A-Z)
        self.symbols    = {}            # знаки стоящие после слов
        self.words      = []
        self.length     = 0             # кол-во слов
        self.text       = text          # оригинальный текст
        self.span_ps    = []            # границы частей предложения (end-1 || < end)
        self.span_w     = []            # границы слов
        self.span_s     = []            # границы предложений

        self.flags      = (lower, )
        self._parser(text)

    # ms - modify symbols
    def ms_char_ignore(self, char=' '):
        self.prefix = [''.join(self.prefix[0].split(char)), ''.join(self.prefix[1].split(char))]
        for key in self.symbols:
            self.symbols[key] = ''.join(self.symbols[key].split(char))

    def ms_no_duplicate(self):
        for key in self.symbols:
            self.symbols[key] = _rds(self.symbols[key])

    def g_symbols(self, index, is_p0):
        if is_p0 and index == -1:
            return self.prefix[0]
        elif index < 0 or index not in self.symbols:
            return ""
        return self.symbols[index]

    def get(self, index, is_part_sentences):
        if not self.words or\
           (is_part_sentences and (index < 0 or index >= len(self.span_ps))) or \
           (not is_part_sentences and (index < 0 or index >= len(self.span_s))):
            return ""
        msg = ""
        if is_part_sentences:
            _min, _max = self.span_ps[index]
        else:
            _min, _max = self.span_s[index]
        for i in range(_min, _max):
            msg += self.words[i]
            if i in self.symbols:
                msg += self.symbols[i]
            msg += ' '
        return msg[:-1]

    def g_text_s(self, rew_span):
        return self.g_text(rew_span[0], rew_span[1], rew_span[2])

    def g_text(self, pts, s_left=False, s_right=True):
        if not pts or not self.words:
            return ""
        ret = ""
        if pts[1]-pts[0] > 0:
            ret = self.text[self.span_w[pts[0]][0]:self.span_w[pts[1]-1][1]]
        elif s_left and s_right:
            s_right = False
        if s_left:
            if pts[0]-1 < 0:
                ret = self.prefix[1] + ret
            elif pts[0]-1 in self.symbols:
                ret = self.symbols[pts[0]-1] + ret
        if s_right and pts[1]-1 in self.symbols:
            ret += self.symbols[pts[1]-1]
        return ret

    def g_list(self, is_lower):
        if self.flags[0] == is_lower:
            return self.words
        _list = []
        for span in self.span_w:
            if is_lower:
                _list += [(self.text[span[0]:span[1]]).lower()]
            else:
                _list += [self.text[span[0]:span[1]]]
        return _list

    def _parser(self, text):
        self.words = []
        i, last_span = 0, 0
        for obj in re_word.finditer(text):
            span = obj.span()
            if span[0]-last_span > 0:
                self._add_symbols(text, i, last_span, span[0])
            i += 1
            last_span = span[1]
            self.span_w += [(span[0], span[1])]
            if self.flags[0]:
                self.words += [(text[span[0]:span[1]]).lower()]
            else:
                self.words += [text[span[0]:span[1]]]
        length = len(text)
        if last_span != length or (not self.span_ps and len(self.span_w) > 0) or \
           (self.span_ps and self.span_ps[-1][1] < length):
            self._add_symbols(text, i, last_span, length, True)
        if self.prefix != "":
            self.prefix = [_rds(self.prefix), self.prefix]
        else:
            self.prefix = ["", ""]
        self.length = len(self.span_w)
        if self.length == 0:
            self.span_ps = None
            self.span_s = None
            self.span_w = None
        else:   # составим конец и начало предложений
            last_span = 0
            length = len(self.span_ps)
            for i in range(0, length):
                flag = False
                if self.span_ps[i][1]-1 in self.symbols:
                    for char in self.symbols[self.span_ps[i][1]-1]:
                        if char in ".?!;":
                            flag = True
                            break
                if i == length-1 or flag:
                    self.span_s += [[last_span, self.span_ps[i][1]]]
                    last_span = self.span_ps[i][1]

    def _add_symbols(self, text, i, span0, span1, new_sentences=False):
        data = text[span0:span1]
        if i > 0:
            if data != "":
                if i-1 in self.symbols:
                    self.symbols[i-1] += data
                else:
                    self.symbols[i-1] = data
        else:
            self.prefix += data
        if not new_sentences and i-1 in self.symbols:
            for char in self.symbols[i-1]:
                if char in ',.?!():;[]<>{}':
                    new_sentences = True
                    break
        if new_sentences:
            if self.span_ps:
                self.span_ps += [[self.span_ps[-1][1], i]]
            else:
                self.span_ps += [[0, i]]

    # ======== ========= ========= ========= ========= ========= ========= =========
    @staticmethod
    def consist_of(word, chars):
        for char in word:
            if char not in chars:
                return False
        return True
