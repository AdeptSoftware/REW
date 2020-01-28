# 30.12.2019
def _r(value, name):
    class _NamedIntConstant(int):
        def __new__(cls, n, v):
            self = super(_NamedIntConstant, cls).__new__(cls, v)
            self.name = n
            return self

        def __str__(self):
            return self.name

        __repr__ = __str__

    return _NamedIntConstant(name, value)
    # return value


# ======== ========= ========= ========= ========= ========= ========= =========
# Текстовые группы
BORDER                  = _r(0, "BORDER")           # ^ or \E\e or $
WORD                    = _r(1, "WORD")             # \w\d\l\c\p or ~ or literals and digits
SYMBOL                  = _r(2, "SYMBOL")           # \x\s or symbols
# Уникальные группы
NOT                     = _r(3, "NOT")              # !
GROUP                   = _r(4, "GROUP")            # () or (?:)
OR                      = _r(5, "OR")               # [] - only chars (or OBJECTS); (|) or (?:|) - all groups
REPEAT                  = _r(6, "REPEAT")           # {max}, {min,max}, +, *, ?     # Рекурсивно разветвляют поиск (↑t)
# Объекты (Имеют структуру: <> - для WORD и >< - для SYMBOL
REGEX                   = _r(7, "REGEX")            # <\w123> for WORD or >..< for SYMBOL              # RegEx: re/rew
FUNCTION                = _r(8, "FUNCTION")         # # fn() - custom handler for word+symbols

# BORDER
B_BEGIN                 = _r(-2, "B_BEGIN")         # ^
B_END                   = _r(-1, "B_END")           # $
B_EDGE_P                = _r(0,  "B_EDGE_P")        # \e
B_EDGE_S                = _r(1,  "B_EDGE_S")        # \E

# WORD
W_WORD                  = _r(0, "W_WORD")           # \w
W_CYRILLIC              = _r(1, "W_CYRILLIC")       # \c
W_LATIN                 = _r(2, "W_LATIN")          # \l
W_DIGIT                 = _r(3, "W_DIGIT")          # \d
W_PARAMETER             = _r(4, "W_PARAMETER")      # \p

# Прочее
MAX_REPEAT              = 4294967295
DIGITS                  = "0123456789"
ENG_LETTERS             = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
RUS_LETTERS             = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
LETTERS                 = RUS_LETTERS+ENG_LETTERS
PARAMETER_CHARS         = ENG_LETTERS+'_'+DIGITS
ALL_WORD_CHARS          = RUS_LETTERS+PARAMETER_CHARS

# Символы
WHITESPACE              = " \t\n\r\v\f"
REPEAT_CHARS            = "*+?{"
NEGATIVE_CHAR           = '!'
BRACKETS                = "<>(["
CLOSED_BRACKETS         = "><)]"
SPECIAL_CHARS           = "\\^$|~" + BRACKETS + REPEAT_CHARS + NEGATIVE_CHAR

# Группы объектов
IMPOSSIBLE_NOT          = [NOT, REPEAT]
OBJECTS                 = [WORD, SYMBOL, GROUP, OR]
LITERALS                = [WORD, SYMBOL]


ESCAPES = {
    r"\b": [SYMBOL, "\b"],
    r"\f": [SYMBOL, "\f"],
    r"\n": [SYMBOL, "\n"],
    r"\r": [SYMBOL, "\r"],
    r"\t": [SYMBOL, "\t"],
    r"\v": [SYMBOL, "\v"],
    r"\\": [SYMBOL, "\\"]
}

SEQUENCES = {
    r"\E": (BORDER, B_EDGE_S),
    r"\e": (BORDER, B_EDGE_P),
    r"\c": (WORD,   W_CYRILLIC),
    r"\d": (WORD,   W_DIGIT),
    r"\l": (WORD,   W_LATIN),
    r"\w": (WORD,   W_WORD),
    r"\p": (WORD,   W_PARAMETER),
    r"\x": (SYMBOL, None, True),
    r"\s": (SYMBOL, None, False)
}


# Проверка состояния констант  ========= ========= ========= ========= =========
if not (len(BRACKETS) == len(CLOSED_BRACKETS)):
    raise ValueError("BRACKETS and CLOSED_BRACKETS have different length")
