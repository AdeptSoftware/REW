# 30.12.2019
from srew.flags import *
import srew.parse


# создание паттерна
def create(pattern, obj=None, flags=FLAG_IGNORE_CASE):
    srew.parse.assert_pattern(pattern)
    srew.parse.assert_flags(flags)
    return srew.parse.make(pattern, srew.parse.assert_objects(obj), flags).build()


def match(pattern, text, obj=None, flags=FLAG_IGNORE_CASE, span=False):
    return create(pattern, obj, flags).match(text, span=span)


def findall(pattern, text, obj=None, _all=True, flags=FLAG_IGNORE_CASE, span=False):
    return create(pattern, obj, flags).findall(text, span=span)


def get_pattern_map(compiled_pattern_list):
    for p in compiled_pattern_list:
        break
    return None
