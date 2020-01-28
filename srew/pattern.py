# 22.01.2020
from srew.text import TextParser
import srew.flags as _f
import srew.constants as _c
from srew.tokenizer import *


class _PatternTokenizer(Tokenizer, RestorableTokenizer):
    def __init__(self, data, pos=0, s_before=False):
        Tokenizer.__init__(self, data, pos)
        RestorableTokenizer.__init__(self, ("data",))
        self.at         = bool(data[0][0] == _c.BORDER and data[0][1] == _c.B_BEGIN)
        self.s_before   = s_before                  # Перед инициализацией был символ?
        self.s_current  = s_before                  # Текущий элемент является символом
        self.s_first    = None

    def __str__(self):
        return "%-5s%-15s || %-15s || %-15s" % ("%i:" % self.index, self.last, self.cur, self.next)

    def result(self, start, index):
        if start == index and not self.s_first and not self.s_current:
            return None
        return (start+1, index+1), self.s_first, self.s_current

    # _all - все или только видимые в тексте в виде символов
    def is_symbol(self, pattern):
        if not pattern:
            return False
        if pattern[0] in [_c.NOT, _c.REPEAT]:
            return self.is_symbol(pattern[1])
        if pattern[0] == _c.GROUP:
            return self.is_symbol(pattern[1][0])
        return pattern[0] == _c.SYMBOL

    def is_get(self, p, s_p):
        return p is not None and ((not s_p and p[0] != _c.BORDER) or (s_p and self.s_current))

    def is_continue(self, w, end):
        if w.index >= end:
            return False
        s_next = self.is_symbol(self.next)
        # Если есть еще слова или их нет и следующим паттерном является символ (текущий слово)
        # result = w.next is not None or (not self.s_current and s_next)
        result = w.next or ((not self.s_current and s_next) or self.next[0] == _c.BORDER)
        # Сместить на слово если есть еще слова и (следующий слово или символ, но текущий является тоже символом)
        if self.is_get(self.next, s_next):
            w.get()
        self.s_current = s_next
        return result


class Pattern:
    def __init__(self, pattern, data, flags):
        self._pattern = pattern
        self._flags = flags
        self._data = data

    def __str__(self):
        return self._pattern

    # ======== ========= =========   БЛОК СРАВНЕНИЯ   ========= ========= =========
    def _cmp_data(self, data, p, w, pos, end):
        res, backup = self._cycle(data, w.p, w.index+1, end, p.s_current, _backup=True, stop=True)
        if res:
            is_target, p.s_current = p.cur[2], res[2]
            w.restore(backup)
            r = self._step(p, w, pos, end, p.s_current)
            if r and is_target:
                return res[0], p.is_symbol(data[0]), p.is_symbol(data[-1])
            return r
        return None

    @staticmethod
    def _check_word(obj, text):
        if obj == _c.W_WORD:        # По сути любое слово
            return TextParser.consist_of(text, _c.LETTERS)
        elif obj == _c.W_PARAMETER:
            return TextParser.consist_of(text, _c.PARAMETER_CHARS)
        elif obj == _c.W_CYRILLIC:
            return TextParser.consist_of(text, _c.RUS_LETTERS)
        elif obj == _c.W_LATIN:
            return TextParser.consist_of(text, _c.ENG_LETTERS)
        elif obj == _c.W_DIGIT:
            return text.isnumeric()
        elif obj is None:           # По сути любой элемент из TextParser.words
            return True
        return obj == text

    def _check_symbol(self, p, w, obj):
        sym = w.p.g_symbols(w.index, not p.index)
        if obj is None and not p.cur[2]:
            return sym != ""
        if obj and sym:
            if self._flags & _f.FLAG_IGNORE_S_ORDER:
                return TextParser.consist_of(obj, sym)
            return sym[:len(obj)] == obj
        return sym == (obj or "")

    def _check(self, p, w, pattern):
        if pattern[0] == _c.BORDER:
            if pattern[1] < 0:
                return (pattern[1] == _c.B_BEGIN and w.index < 0) or (pattern[1] == _c.B_END and not w.next)
            return w.is_ps(pattern[1] == _c.B_EDGE_S)
        elif pattern[0] == _c.WORD:
            return self._check_word(pattern[1], w.cur)
        elif pattern[0] == _c.SYMBOL:
            return self._check_symbol(p, w, pattern[1])
        elif pattern[0] == _c.NOT:
            return not self._check(p, w, pattern[1])
        elif pattern[0] == _c.REGEX:
            if pattern[2]:
                return pattern[1].search(w.p.g_symbols(w.index, not p.index)) is not None
            else:
                return pattern[1].search(w.cur) is not None
        elif pattern[0] == _c.FUNCTION:
            return pattern[1](w.p, w.index, not p.index)
        # Достигнет лишь по вине разработчика
        raise SyntaxError("Unknown pattern code at position %i (opcode: %s)" % (p.index, str(pattern[0])))

    def _repeat(self, p, w, pos, end):
        res = None
        i, _max = 0, p.cur[2][1]
        if not p.next and p.cur[2][2]:
            _max = p.cur[2][0]
        while i < _max:
            if i >= p.cur[2][0]:
                backup_w, backup_p = w.backup(), p.backup()
                ret = self._step(p, w, pos, end, p.s_current)
                if ret:
                    if backup_p["cur"][2][2]:
                        return ret
                    res = ret or res
                w.restore(backup_w)
                p.restore(backup_p)
            if p.cur[1][0] == _c.BORDER:        # Только положительные
                if not w.seek_ps(p.cur[1][1] == _c.B_EDGE_S):
                    break
                print(w.index, w.cur)
            else:
                ret, backup = self._cycle((p.cur[1],), w.p, w.index+1, end, p.s_current, _backup=True, stop=True)
                if ret:
                    p.s_current = ret[2]
                    w.restore(backup)
                else:
                    break
            i += 1
        if i >= p.cur[2][0]:
            return self._step(p, w, pos, end, p.s_current) or res
        return None

    def _single_or(self, p, w, pos, end):
        backup = w.backup()
        for obj in p.cur[1][0]:
            s_next = p.is_symbol(obj)
            if p.is_get(obj, s_next):
                w.get()
            if (w.cur is not None or obj[0] == _c.BORDER) and self._check(p, w, obj):
                p.s_current = s_next
                return self._step(p, w, pos, end, p.s_current)
            w.restore(backup)
        return None

    # Если выполняется, то вызываем следующий шаг
    def _step(self, p, w, pos, end, s_first=None):
        p.s_first = p.s_first or s_first
        if not p.next or (p.cur and p.cur[0] == _c.BORDER and p.cur[1] == _c.B_END):
            return p.result(pos, w.index)
        if p.next[0] == _c.GROUP:
            p.get()
            return self._cmp_data(p.cur[1], p, w, pos, end)
        elif p.next[0] == _c.OR:
            p.get()
            length = len(p.cur[1])
            if length == 1:
                return self._single_or(p, w, pos, end)
            i, res, p_backup = 0, None, p.backup()
            while not res and i < length:
                res = self._cmp_data(p.cur[1][i], p, w, pos, end)
                if not res and p_backup["index"] != p.index:
                    p.restore(p_backup)
                i += 1
            return res
        elif p.next[0] == _c.REPEAT:
            p.get()
            return self._repeat(p, w, pos, end)
        elif p.is_continue(w, end):
            p.get()
            if self._check(p, w, p.cur):
                return self._step(p, w, pos, end, p.s_current)
        return None

    def _cycle(self, data, t, pos, end, s_before=False, _backup=False, stop=False):
        if data[0][0] == _c.BORDER and data[0][1] == _c.B_BEGIN and pos != 0:
            return None
        if pos < 0:
            pos = 0
        i, length = pos-1, t.length-1+int(len(data) == 1 and not stop and data[0][0] == _c.SYMBOL)
        p = _PatternTokenizer(data, s_before=s_before)
        w = TextParserTokenizer(t, pos, self._flags & _f.FLAG_IGNORE_CASE)
        while i < length:
            p.s_first = None
            backup = w.backup()
            res = self._step(p, w, i, end)
            if res:
                if _backup:
                    return res, w.backup()
                return res
            if stop or p.at:
                break
            if backup["index"] != w.index-1:
                w.restore(backup)
                w.get()
            p.seek(0)
            p.s_current = s_before
            if p.next[0] == _c.BORDER and p.next[1] >= 0:
                w.seek(w.index)
                if not w.seek_ps(p.next[1] == _c.B_EDGE_S):
                    break
                i = w.index
                continue
            i += 1
        if _backup:
            return None, None
        return None

    # ======== ========= ======  ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ  ====== ========= =========
    def _str2parser(self, string):
        if type(string) is not TextParser:
            string = TextParser(string, self._flags & _f.FLAG_IGNORE_CASE)
        if len(string.flags) == 1:
            if self._flags & _f.FLAG_IGNORE_SPACE:
                string.ms_char_ignore(' ')
            if self._flags & _f.FLAG_IGNORE_S_DUPLICATE:
                string.ms_no_duplicate()
            string.flags = (string.flags[0],
                            self._flags & _f.FLAG_IGNORE_SPACE,
                            self._flags & _f.FLAG_IGNORE_S_DUPLICATE)
        if string.length == 0:
            return None
        return string

    @staticmethod
    def _span2string(span, t, ret_span):
        if ret_span:
            return span
        return span[0], t.g_text_s(span)

    # ======== ========= =========   СПОСОБЫ ПОИСКА   ========= ========= =========
    def match(self, t, start=0, end=_c.MAX_REPEAT, _span=False):
        t = self._str2parser(t)
        if t:
            return self._span2string(self._cycle(self._data, t, start, end), t, _span)

    def findall(self, t, start=0, end=_c.MAX_REPEAT, overlap=False, _span=False):
        spans, t = [], self._str2parser(t)
        while t:
            span = self._cycle(self._data, t, start, end)
            if not span:
                break
            spans += [self._span2string(span, t, _span)]
            if span[0][0] == span[0][1]:
                start = span[0][1]+1
                continue
            offset = span[0][not overlap]+int(overlap)
            if start >= offset:
                start += 1
            else:
                start = offset
        return spans
