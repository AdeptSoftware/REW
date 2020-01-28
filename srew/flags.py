# Flags
FLAG_NULL                           = 0
FLAG_IGNORE_CASE                    = 1     # Не учитывать регистр букв
FLAG_IGNORE_SPACE                   = 2     # Игнорировать пробел в символах    " , : ;."        -> ",:;."
FLAG_IGNORE_S_ORDER                 = 4     # Игнорировать порядок символов     ")." => ")." = ".)" = " )." = " ) . "
FLAG_IGNORE_S_DUPLICATE             = 8     # Убирает дубли символов            ".  :))" => ". :)"


""" # Работает только так:
x = CND_ONE_SPACE_IN_ROW+CND_CASE_SENSITIVE
print(x & FLAG_IGNORE_CASE)
print(x & FLAG_IGNORE_CASE and x & FLAG_IGNORE_SPACE)
print(x & FLAG_IGNORE_CASE and x & FLAG_IGNORE_SPACE)
print(x & FLAG_IGNORE_SPACE)
"""
