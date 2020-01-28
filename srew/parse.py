# 30.12.2019
from srew.pattern import Pattern, Tokenizer
import srew.constants as _c
import srew.flags as _f
import re


_FLAG_OR               = 2**25


def assert_pattern(pattern):
    if type(pattern) is not str:
        raise TypeError("Pattern must be string")
    if not pattern:
        raise ValueError("Pattern is empty")


def assert_flags(flags):
    if type(flags) is not int:
        raise TypeError("Flags must be integer")


def assert_objects(objects):        # possible objects = [r"0", f, zx, ["1", f, "d", zx]]
    if not objects:
        return None
    is_list = type(objects) is list
    if is_list:
        _list = []
    else:
        _list = {}
    for e in objects:
        if is_list:
            obj = e
        else:
            obj = objects[e]
        # Проверим каждый объект
        if type(obj) is list:
            obj = list([_opcode(e_obj), e_obj] for e_obj in obj)
            _type = _c.OR
        else:
            _type = _opcode(obj)
        # Сохраним результаты проверки
        if is_list:
            _list += [(_type, obj)]
        else:
            _list[e] = (_type, obj)
    return _list


def _opcode(obj):
    if callable(obj):
        return _c.FUNCTION
    elif str(type(obj)) == "<class 're.Pattern'>" or type(obj) is Pattern:
        return _c.REGEX
    elif type(obj) is str:
        if not obj:
            raise SyntaxError("Objects (string) mustn't be empty!")
        return -1
    else:
        raise ValueError("Unsupported element of object list: " + str(obj))


# ======== ========= ========= ========= ========= ========= ========= =========
class _Tokenizer(Tokenizer):       # Оптимизировать как-нибудь потом
    def _next(self, is_skip=None):
        try:
            char = self.data[self.index+2]
            self.index += 1
            if char == '\\':
                try:
                    char += self.data[self.index + 2]
                    self.index += 1
                except IndexError:
                    raise IndexError("Bad escape (end of pattern): " + str(self.data))
        except IndexError:
            char    = None
        this = self.next
        self.next = char
        return this

    def match(self, char):
        if self.next == char:
            self._next()
            return True
        return False

    def pos(self):
        return self.index+2-len(self.next or '')


# ======== ========= ========= ========= ========= ========= ========= =========
class _PatternBuilder(Pattern):
    def __init__(self, pattern, flags):
        super().__init__(pattern, None, flags)
        self.concat = True
        self.new    = False
        self._data  = []

    def _err(self, pos, left=1, right=1):
        if pos-left < 0:
            left = 0
        return _err(pos) + (" \"%s\"" % self._pattern[pos-left:pos+right])

    def append(self, obj, pos):
        if obj == [_c.SYMBOL, ' '] and self._flags & _f.FLAG_IGNORE_SPACE:
            if not (self._data and self._data[-1][0] == _c.BORDER):
                self.new = True
            return
        if not self.new and self.concat:
            if self._data:
                if obj[0] == _c.BORDER:
                    if self._data[-1][0] == _c.BORDER:
                        raise SyntaxError("Duplicate border symbol" + _err(pos))
                    if obj[1] == _c.B_BEGIN:
                        raise SyntaxError("Start of line character must be at the beginning, but" + self._err(pos))
                    if obj[1] == _c.B_END and pos < len(self._pattern)-1:
                        raise SyntaxError("End of line character must be at the end of string, but" + self._err(pos))
                if obj[0] == _c.REPEAT:
                    if self._data[-1][0] == _c.REPEAT:
                        raise SyntaxError("Multiple repeat" + self._err(pos))
                    if (self._data[-1][0] == _c.BORDER and self._data[-1][1] < 0) or \
                       (self._data[-1][0] == _c.NOT and self._data[-1][1] is None):
                        raise SyntaxError("Impossible repeat" + self._err(pos))
                    self._data[-1] = (obj[0], _tuple(self._data[-1]), obj[2])
                    return
                if not self._data[-1][1]:
                    if self._data[-1][0] == _c.NOT:
                        if obj[0] in _c.IMPOSSIBLE_NOT:
                            raise SyntaxError("Negative char" + self._err(pos))
                        self._data[-1] = (_c.NOT, _tuple(obj))
                        return
                elif _is_concat(self._data[-1], obj):
                    self._data[-1][1] += obj[1]
                    return
            else:
                if obj[0] == _c.BORDER and obj[1] == _c.B_END:
                    raise SyntaxError("End of line character" + self._err(pos))
                if obj[0] == _c.REPEAT:
                    raise SystemError("Nothing to repeat" + self._err(pos))
        if self.new:
            self.new = False
            if obj[0] == _c.SYMBOL:
                self._data += [(_c.SYMBOL, None, False)]
        self._data += [obj]

    def prepare(self):
        for i in range(len(self._data)):
            if self._data[i][0] in _c.LITERALS and type(self._data[i]) is not tuple:
                self._data[i] = (self._data[i][0], self._data[i][1])
        res = _or(self._data)
        if res:
            self._data = [res]

    def subpattern(self):
        return tuple(obj for obj in self._data)

    def build(self):
        if len(self._data) == 1 and self._data[0][0] == _c.GROUP:
            self._data = tuple(obj for obj in self._data[0][1])
        # tuple(print(obj) for obj in self._data)     # Для отладки
        return Pattern(self._pattern, _tuple(self._data), self._flags)


# ======== ========= ========= ========= ========= ========= ========= =========
def make(pattern, obj, flags):
    p = _PatternBuilder(pattern, flags)
    source = _Tokenizer(pattern)
    p.concat = not (flags & _FLAG_OR)
    while source.next:
        pos = source.pos()
        p.append(_parse(source, pattern, obj, flags), pos)
    p.prepare()
    return p


def _err(pos):
    return " at position %i" % pos


def _parse(source, pattern, obj, flags):
    char = source.get()
    is_list = obj and type(obj) is list
    if not (flags & _FLAG_OR):
        if char in _c.NEGATIVE_CHAR:
            return [_c.NOT, None]
        elif char in _c.BRACKETS:
            br, pos, i = 0, source.pos(), _c.BRACKETS.index(char)
            while source.next:
                char = source.get()
                if char in _c.CLOSED_BRACKETS[i] and br == 0:
                    content = pattern[pos:source.pos()-1]
                    if not content:
                        return [_c.SYMBOL, _c.BRACKETS[i] + _c.CLOSED_BRACKETS[i]]
                    if _c.OBJECTS[i] in _c.LITERALS:
                        if content[0] == '#':           # Виды объектов: FUNCTION, OR, REGEX, None (WORD/SYMBOL)
                            if not obj:
                                raise SyntaxError("Object list is empty!")
                            key = content[1:]
                            if is_list:
                                key = int(key)
                            return _object(obj[key], bool(i))
                        return _c.REGEX, re.compile(content), bool(i)
                    else:
                        target = False  # Определим нужен таргет или нет
                        if _c.OBJECTS[i] == _c.GROUP and content[:2] == '?:':
                            content = content[2:]
                            if not content:
                                raise SyntaxError("Group is empty" + _err(pos))
                            target = True
                        res = make(content, obj, flags+(_FLAG_OR*bool(_c.OBJECTS[i] == _c.OR))).subpattern()
                        if _c.OBJECTS[i] == _c.GROUP:
                            if len(res) == 1:
                                if res[0][0] == _c.OR:
                                    return res[0][0], res[0][1], target
                            return _c.GROUP, res, target
                        if _c.OBJECTS[i] == _c.OR:
                            res = (res,)
                        return _c.OBJECTS[i], res
                br += int(char == _c.BRACKETS[i]) - int(char == _c.CLOSED_BRACKETS[i])
            raise ValueError("'%s' isn't closed%s" % (_c.BRACKETS[i], _err(pos)))
        elif char in _c.REPEAT_CHARS:
            pos = source.pos()
            if char == '?':
                _min, _max = 0, 1
            elif char == '*':
                _min, _max = 0, _c.MAX_REPEAT
            elif char == '+':
                _min, _max = 1, _c.MAX_REPEAT
            elif char == '{':
                if source.next == '}':
                    source.get()
                    return [_c.SYMBOL, "{}"]
                _min, _max = 0, _c.MAX_REPEAT
                lo = hi = ""
                while source.next in _c.DIGITS:
                    lo += source.get()
                if source.match(','):
                    while source.next in _c.DIGITS:
                        hi += source.get()
                else:
                    hi = lo
                if not source.match('}'):
                    source.seek(pos)
                    return [_c.SYMBOL, char]
                if lo:
                    _min = int(lo)
                if hi:
                    _max = int(hi)
                if _min > _c.MAX_REPEAT or _max > _c.MAX_REPEAT:
                    raise OverflowError("The repetition number is too large" + _err(pos))
                if _max < _min:
                    raise SyntaxError("Min repeat < max repeat" + _err(pos))
            else:
                raise AssertionError("Unsupported quantifier %s%s" % (char, _err(pos)))
            return [_c.REPEAT, None, (_min, _max, source.match('?'))]
        elif char == '|':
            return _c.OR, None
    if char in _c.WHITESPACE:
        return [_c.SYMBOL, char]
    elif char[0] == '\\':
        return _escape(char)
    elif char == '^':
        return _c.BORDER, _c.B_BEGIN
    elif char == '$':
        return _c.BORDER, _c.B_END
    elif char == '~':
        return _c.WORD, None
    elif char not in _c.ALL_WORD_CHARS:
        return [_c.SYMBOL, char]
    else:
        if flags & _f.FLAG_IGNORE_CASE:
            char = char.lower()
        return [_c.WORD, char]


def _escape(escape):
    code = _c.SEQUENCES.get(escape)
    if code:
        return code
    code = _c.ESCAPES.get(escape)
    if code:
        return code
    if escape[1] in _c.SPECIAL_CHARS:
        return [_c.SYMBOL, escape[1]]
    raise ValueError("Bad escape " + escape)


def _or(objects):
    pos, last = [], 0
    for i in range(len(objects)):
        if objects[i][0] == _c.OR and objects[i][1] is None:
            pos += [(last, i)]
            last = i+1
    if pos:
        pos += [(last, len(objects))]
        return _c.OR, tuple(_tuple(objects[span[0]:span[1]]) for span in pos)
    return None


def _object(obj, is_sym, is_list=False):
    if obj[0] == -1:
        for char in obj[1]:
            if (char not in _c.ALL_WORD_CHARS) != is_sym:
                raise ValueError("\"%s\" isn't %s type" % (obj[1], ("word", "symbol")[is_sym]))
        return _c.LITERALS[is_sym], obj[1]
    if obj[0] == _c.FUNCTION:
        return obj[0], obj[1]
    if obj[0] == _c.REGEX:
        return obj[0], obj[1], is_sym
    if obj[0] == _c.OR:
        if is_list:
            raise ValueError("Invalid nesting level (i > 1).\nExample: [str, re, fn, [str, re, fn]]")
        return _c.OR, (tuple(_object(e, is_sym, True) for e in obj[1]),)
    raise TypeError("Object type (opcode: %i) isn't support!" % obj[0])


def _tuple(_list):
    return tuple(obj for obj in _list)


def _is_concat(last, new):
    if last[0] in _c.LITERALS and new[0] in _c.LITERALS and last[0] == new[0] and \
       type(last[1]) is str and type(new[1]) is str:
        return True
    return False
