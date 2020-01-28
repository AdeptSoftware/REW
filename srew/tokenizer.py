# 03.01.2020


class Tokenizer:
    def __init__(self, data, pos=0):
        self.data   = data
        self.next   = None
        self.index  = -2
        self.seek(pos)

    # def __str__(self): return "%-5s%-15s%-15s%-15s" % ("%i:" % self.index, self.last, self.cur, self.next)

    def _get(self, pos):
        if pos < 0:
            return None
        try:
            return self.data[pos]
        except IndexError:
            return None

    def _next(self, is_skip):
        if not is_skip:
            self.last = self.cur
            self.cur  = self.next
        else:
            self.last = self._get(self.index)
            self.cur  = self._get(self.index+1)
        self.next = self._get(self.index+2)
        self.index += 1
        return self.cur

    def get(self):
        return self._next(False)

    def seek(self, pos):
        self.index = pos-2
        self._next(True)


class RestorableTokenizer:
    def __init__(self, keys):
        self._keys = keys

    def backup(self):
        state = {}
        for key in self.__dict__.keys():
            if key not in self._keys and key != "_keys":
                state[key] = self.__dict__[key]
        return state

    def restore(self, state):
        for key in (state or []):
            self.__setattr__(key, state[key])


class TextParserTokenizer(Tokenizer, RestorableTokenizer):
    def __init__(self, p, pos, is_lower=True):
        self.p = p                                     # TextParser
        Tokenizer.__init__(self, p.g_list(is_lower), pos)
        RestorableTokenizer.__init__(self, ("p", "data"))
        self._update_ps(pos-1)

    def __str__(self):
        return "%-5s%-6s%-6s%-15s%-15s%-15s" % ("%i:" % self.index, "pi=%i" % self.pi, "si=%i" % self.si,
                                                self.last, self.cur, self.next)

    def get(self):
        if self.index+1 < self.p.span_s[-1][1]:
            if self.p.span_ps[self.pi][1] == self.index+1:
                self.pi += 1
            if self.p.span_s[self.si][1] == self.index+1:
                self.si += 1
        # print("%-7s si=%-2i pi=%-2i %s" % ("w[%i]:" % self.index, self.si, self.pi, self.next))
        return super().get()

    # Перемотка относительно span'а
    @staticmethod
    def _span_pos(pos, spans):
        for i in range(len(spans)):
            if spans[i][0] <= pos < spans[i][1]:
                return i
        return len(spans)-1     # None

    def _update_ps(self, pos):
        if pos < 0:
            pos = 0
        self.pi = self._span_pos(pos, self.p.span_ps)     # Позиция относительно части предложения
        self.si = self._span_pos(pos, self.p.span_s)      # Позиция относительно предложения

    def seek(self, pos):
        super().seek(pos)
        self._update_ps(pos-1)

    def __get(self, s):
        if s:
            return self.si, self.p.span_s
        return self.pi, self.p.span_ps

    def __is_ps(self, ps):
        return ps[1][ps[0]][0]-1 == self.index or ps[1][ps[0]][1]-1 == self.index

    # Переместить позицию в следующее начало[end=0] / конец[end=1] предложения[s=1] (или его части[s=0])
    def seek_ps(self, s, offset=1):
        index, span = self.__get(s)
        if offset != 0:
            if self.index + 1 == span[index][1]:
                index += 1
            index += offset-1
            if self.index < -1:
                index -= 1
            if index < 0:
                self.seek(0)
                return True
        try:
            self.seek(span[index][1])
        except IndexError:
            self.seek(len(self.data))
            return False
        return True

    # Является ли текущая позиция началом[end=0] / концом[end=1] предложения[s=1] (или его части[s=0])
    def is_ps(self, s):                        # edge:    |012|3456|789AB|
        return self.__is_ps(self.__get(s))
