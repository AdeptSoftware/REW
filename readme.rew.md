# Regular Expressions for Words (REW v1.0)

# Специальные последовательности и ключевые символы
^   - Начало текста

$   - Конец текста

\E  - Граница предложения (завершено '.', '?' или '!')

\e  - Граница части предложения (любой символ кроме букв, цифр и '_')

!   - Отрицание (нельзя отрицать отрицание и повторение)

()  - Группировка. (?:) - для выделения нужного участка. (|) - для "или"

{}  - квантификаторы такие же как в Regular Expression

\w  - слово, состоящее из букв англ+рус алфавита

\c  - слово, состоящее только из рус алфавита

\l  - слово, состоящее только из англ алфавита

\d  - слово, состоящее только из цифр

\p  - слово-параметр (англ_цифры)

\x  - отсутствие символов

\s  - любой символ

~   - любое слово



P.S.: ^$\E\e - не могут стоять друг за другом в некоторых случая. Кроме того, это бессмысленно.


# Флаги
FLAG_NULL               - Без флагов

FLAG_IGNORE_CASE        - Не учитывать регистр букв

FLAG_IGNORE_SPACE       - Игнорировать пробел в символах    " , : ;." -> ",:;."

FLAG_IGNORE_S_ORDER     - Игнорировать порядок символов     ")." => ")." = ".)" = " )." = " ) . "

FLAG_IGNORE_S_DUPLICATE - Убирает дубли символов            ".  :))" => ". :)"



Используются в rew.create, rew.match, rew.findall

Пример:

            rew.create(r".?(?:~+?).", None, rew.FLAG_IGNORE_CASE+rew.FLAG_IGNORE_SPACE)


# Использование объектов
            obj = [r",+", fn, re_obj, ["1", "0", fn, re_obj]]
            rew.create(pattern, obj)

obj[0]    - любой текст, преобразуется в регулярное выражение (регулярное выражение (re))

obj[1]    - функция, имеющая прототип
            
            def fn(TextParser, pos, is_pattern_0): return True/False
            # is_pattern_0 - необходим для получения prefix в TextParser.g_symbols()
            
obj[2]    - re/REW

obj[3]    - список, вернет True если один из элементов вернет True

obj[3][0] - слово/символ зависит от того как вызывать объект

P.S.: Поддерживается только 1 уровень вложенности


- Как вызывать объекты:

            pattern = r"<#2><#3>"   - проверять как слово
            pattern = r">#0<"       - проверять как символ

- Функции не поддерживают разделение на символы и слова.

- Если obj[3][0] или obj[3][1] будет символом, а вызов был <#3> (как слово), то возникнет исключение



# TextParser
Разбивает предложение на слова, отдельно от символов

TextParser.prefix[0]  - символы (без повторений) перед первым словом в тексте

TextParser.prefix[0]  - символы (с повторениями) перед первым словом в тексте

TextParser.symbols    - символы (только в позициях, в которых они есть)

TextParser.words      - все слова

TextParser.length     - длина TextParser.words и TextParser.span_w

TextParser.text       - исходный текст

TextParser.span_ps    - граница частей предложений

TextParser.span_s     - граница предложений

TextParser.span_w     - граница слов

TextParser.ms_char_ignore()   - в TextParser.prefix и TextParser.symbols удаляет указанный символ

TextParser.ms_no_duplicate()  - убирает в TextParser.prefix и TextParser.symbols все дублирующие символы

TextParser.get()              - получить предложений/его часть по индексу

TextParser.g_symbols()        - получить символ по позиции

TextParser.g_text()           - получить текст по диапазону индексов pts (можно добавить символы слева/справа)

TextParser.g_text_s()         - тоже самое что и предыдущее, но для REW

TextParser.g_list()           - выдает список слов с нужным регистром

TextParser.consist_of()       - проверяет состоит ли слово из указанных символов (статический метод)


# Другие примеры
1:

            import rew
            p = rew.create(pattern)
            p.match(string)
            p.findall(string)

2:

            import rew
            rew.match(pattern, string)
            rew.findall(pattern, string)

3: Менее затратный способ получения предложений

            t = rew.text.TextParser(string)
            for span in t.span_s:
                print(t.text[t.span_w[span[0]][0]:t.span_w[span[1]-1][1]])

4:

            import rew
            res = rew.findall(r"\E(?:it's ~+?\E)", "It's a Bird... It's a Plane... It's Superman!")
            for obj in res:
                print("'%s' start at pos %i" % (obj[1], obj[0][0]))
            
            # Результат работы:
            'It's a Bird' start at pos 0
            'It's a Plane' start at pos 4
            'It's Superman' start at pos 8
            
            # Нумерация слов (w) и символов (s) в тексте:
            string = ":) It's a Bird... It's a Plane... It's Superman!"
            w:           0  1 2  3      4  5 6   7      8  9     10
            s:        0    1 2 3     4    5 6 7      8    9 10        11
            
5:

            t = rew.text.TextParser(string)
            res = p.match(t, 2, 10)                         # поиск со слова 2 до 10
            if res:                                         # в случае неудачи вернет None
                print("'%s' start at pos %i" % (res[1], res[0][0]))
    
6:

            res = p.findall(t, overlap=True, _span=True)    # c перекрытием при поиске
            for obj in res:                                 # в случае неудачи вернет []
                print("'%s' start at pos %i" % (t.g_text_s(obj), obj[0][0]))
