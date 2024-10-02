import os
import pdb
import sys
import codecs
import re
import argparse

from bs4 import BeautifulSoup
from bs4 import Comment

from collections import Counter

import html2text

import langid
import roman

import UnicodeNormalizer as uni


#####################################
class NonEnglishException(Exception):
    pass


def incrementListItemCallback(m):
    if re.search(r'^[0-9]+$', m.group(0)):  # Digit
        return str(str(int(m.group(0)) + 1))
    elif re.search(r'^[a-z]$', m.group(0)):
        return 'a' if m.group(0) == 'z' else str(str(chr(ord(m.group(0)) + 1)))
    elif re.search(r'^[A-Z]$', m.group(0)):
        return 'A' if m.group(0) == 'Z' else str(str(chr(ord(m.group(0)) + 1)))
    else:
        print('Error', m)
    return m


def spaceParenCallback(m):
    return re.sub(r'\)', ') ', m.group(0))


def spacePunctCallback(m):
    return '{} {}'.format(m.group(0)[:-1], m.group(0)[-1])


def incrementListItemCallbackRoman(m):
    nRoman = roman.toRoman(roman.fromRoman(m.group(0).upper()) + 1)
    return nRoman if m.group(0)[0].isupper() else nRoman.lower()


class HtmlPreprocessor:

    def __init__(self, filename):
        # 将html转为字符串返回
        def loadRawHtml(filename):
            # Try UTF-8
            try:
                return '\n'.join([line for line in codecs.open(filename, 'rb', 'utf-8')])
            except UnicodeDecodeError:
                return '\n'.join([line for line in codecs.open(filename, 'rb', 'windows-1252')])

        # Load html
        html = loadRawHtml(filename)

        # Unescape the html first, we can have unicode html (e.g., &gt;p&lt; --> <p>)
        # html_parser = HTMLParser()
        # html = html_parser.unescape(html)

        # Parse with bs4
        self.soup = BeautifulSoup(html, 'html.parser')

        # 去掉注释
        comments = self.soup.findAll(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment.extract()

        # Holds popup elements that need to be relocated, as they can interrupt sentences
        self.popups = []

    def process(self):
        def isIteratable(element):
            return 'childGenerator' in dir(element)

        def isSkippableElement(element):
            def isSpanScreenReaderOnlyElement(element):
                return element.name == 'span' and element.get('class') is not None and 'sr-only' in element.get(
                    'class')

            def isIgnoredElement(element):
                return element.name in ['style', 'script', 'nav', 'video', 'select', 'head', 'header', 'footer']

            def isNavigationLink(element):
                return element.name == 'a' and re.search(
                    r'^<a\s.*>(Learn\sMore|(Back|Return)([\-\s]to[\-\s]Top)?|Skip\sto\s(content|navigation))</a>$',
                    str(element), flags=re.IGNORECASE)

            ############
            return isSpanScreenReaderOnlyElement(element) or isNavigationLink(element) or isIgnoredElement(element)

        # Most likely pop-up elements if set display:none. These can interrupt the sentence, so we have to relocate the elements
        def isPopupElement(element):
            return element.name in ['span', 'div'] and element.get(
                'style') is not None and 'display:none' in element.get('style')

        def isListItem(element):
            return element.name == 'li'

        def processHtml(self, element, listItemDepth=0):
            if isIteratable(element):
                if isListItem(element):
                    listItemDepth += 1

                for child in element.childGenerator():
                    name = getattr(child, "name", None)
                    if name is not None:  # Container
                        if isSkippableElement(child):  # Skip parsing this element
                            child.extract()
                            continue
                        # TODO check pop ups
                        processHtml(self, child, listItemDepth if not isPopupElement(child) else 0)
                        if isPopupElement(child):
                            # Create paragraph tag and set aside to insert at end of body
                            newTag = self.soup.new_tag('p')
                            newTag.append(child.extract())
                            self.popups.append(newTag)
                            continue
                    elif not child.isspace() and listItemDepth > 0:
                        # Annotate list items, as we can have paragraphs embedded and we want to associate it correctly!
                        BEGIN_TAG = '&lt;LISTITEM depth="%d"&gt;' % (listItemDepth,)
                        child.replaceWith(''.join([BEGIN_TAG, str(child), '&lt;/LISTITEM&gt;']))

        #####################################
        for child in self.soup.childGenerator():
            processHtml(self, child)

        # Finally, re-insert the popups at the end of the body
        body = self.soup.find('body')
        for element in self.popups:
            body.append(element)
        # with open('./tmp/tmp.html', 'w', encoding='utf-8') as fwite:
        #     fwite.write(str(self.soup))
        return str(self.soup)


#####################################

class TextPostProcessor:

    def __init__(self, document):
        self.document = document

    def ensureSingleSpaced(self, text):
        return re.sub(r'\s+', ' ', text)

    def containsLettersOrNumbers(self, text):
        return bool(re.search(r'\w', text))

    # Detects language for each paragraph and returns max (per document seems less accurate from initial tests)
    def langDetect(self, text):
        langs = [langid.classify(line)[0] for line in text if len(line.strip()) > 0]
        data = Counter(langs)
        return [l for l, cnt in data.most_common(1)]

    def handleInlineList(self, text):
        # print(text)
        # Just strip for now...
        # if re.search(r':\s*(\(\s*([0-9][0-9]?|[A-Za-z]+)\s*\)|([0-9][0-9]?|[A-Za-z])(\s*\)|\.|\\\.))\s*', text):
        text = re.sub(r'\s+(\(\s*([0-9][0-9]?|[A-Za-z]+)\s*\)|([0-9][0-9]?|[A-Za-z])(\s*\)|\.|\\\.))\s*', ' ',
                      text)
        text = re.sub(r'\s+(ix|iv|v?i{1,3})\.\s+', ' ', text, re.IGNORECASE)
            # print(text)
        # print(text[:20])
        return text

    def postProcess(self):
        def stripPlaintextListFormatters(text):
            text = re.sub('(\s+|^)(\*|\-|\+|\\\-|\\\+|\u2022|\u00B7|\u2013|\u25CF|\u2714|>)\s+', ', ', text,
                          re.UNICODE)
            text = re.sub(r'^(,)?\s+', '', text)
            text = re.sub(r'(\s+|^)([0-9][0-9]?\.)+[0-9][0-9]?\s+', ' ', text)

            text = re.sub(r'(\s+|^)(\(\s*([0-9][0-9]?|[A-Za-z]+)\s*\))\s+', ' ', text)
            text = re.sub(r'([;\.\?:!]\s+|^)([0-9][0-9]?|[A-Za-z])(\s*\)|\.|\\\.)\s+',
                          lambda m: re.sub(r'(\s+|^)([0-9][0-9]?|[A-Za-z])(\s*\)|\.|\\\.)', ' ', m.group(0)), text)

            text = re.sub(r'\s*(ix|iv|v?i{1,3})\.\s+', ' ', text, re.IGNORECASE)

            text = re.sub(r'^([0-9]+\.[0-9]+)+\.?', ' ', text)
            text = re.sub(r'^\s+', '', text)
            # FIXME: Fix regular express and remove and not condition
            if re.search(
                    r'(\s+|^)((\*|\-|\+|\\\-|\\\+|\u2022|\u00B7|\u2013|>)|(([0-9][0-9]?\.)+[0-9][0-9]?)|(\(\s*([0-9][0-9]?|[A-Za-z]+)\s*\)|([0-9][0-9]?|[A-Za-z])(\s*\)|\.|\\\.)))\s+',
                    text) and not re.search(r'(\s+|^)([0-9][0-9]?|[A-Za-z])(\s*\)|\.|\\\.)\s+', text):
                return stripPlaintextListFormatters(text)
            return text

        if 'en' not in self.langDetect(self.document):
            raise NonEnglishException('Document is not English')

        res = []
        for i, line in enumerate(self.document):
            # If empty line or doesn't contain any characters, then skip...
            # Note that this also skips lines in languages with other character sets (Russian, Chinese, Korean, Arabic)
            if len(line.strip()) == 0 or not self.containsLettersOrNumbers(line):
                continue

            line = uni.normalize(line)

            # TODO should we exclude non-English paragraphs?
            # if langid.classify(line)[0] != u'en':
            #	continue

            # Remove double white spaces
            line = self.ensureSingleSpaced(line)
            # Fix plural(s)
            line = re.sub(r'\(s\)', 's', line)
            # Replace and/or with and
            line = re.sub(r'\sand/or\s', ' and ', line)

            line = re.sub(r'\\.', '.', line)

            # Replace URLs
            line = re.sub(r'http(s)?://[^\s]+', 'website_url_lnk', line)
            line = re.sub(r'www\.[^\s]+', 'website_url_lnk', line)

            line = re.sub(r'\s*\|\s*', '. ', line)
            line = re.sub(r'\s*\.', '.', line)
            line = re.sub(r'^\s*[\.,;:]\s*', '', line)
            # Ensure list items spaced after colon ":(1)" --> ": (1)"
            line = re.sub(r':\(', ': (', line)


            # Ensure spaces after end paren (e.g., ")if" --> ") if"
            line = re.sub(r'\)[A-Za-z0-9]', spaceParenCallback, line)

            # Just in case we messed anything up before
            line = self.ensureSingleSpaced(line)

            if ':' in line:
                line = self.handleInlineList(line)

            # Remove numbering, such as (1) or 1.2.3
            line = stripPlaintextListFormatters(line)

            # Fix punctuation spacing
            line = re.sub(r'(:,|:\.|:+)', ':', line)
            line = re.sub(r',\.', ',', line)
            line = re.sub(r'(;,|;+)', ';', line)
            line = re.sub(r',+', ',', line)
            line = re.sub(r'(\)\.|;|,)[A-Za-z]', spacePunctCallback, line)
            line = re.sub(r'(\.|\?)[A-Z]', spacePunctCallback, line)

            # Strip any left over headers..
            line = re.sub(r'^\s*#+\s*', '', line)

            line = self.ensureSingleSpaced(line)
            # Strip white space at beginning of line
            line = re.sub(r'^\s+', '', line)
            # Don't let lines end with semicolons
            line = re.sub(r';$', '.', line)

            res.append(line)
        return res


#####################################

class Preprocessor:
    def __init__(self, filename):
        html = HtmlPreprocessor(filename).process()
        h2text = html2text.HTML2Text()
        h2text.body_width = 0
        h2text.ignore_links = True  # Do not include links
        h2text.ignore_images = True  # Do not include images
        h2text.ignore_emphasis = True  # Do not include bold and italics formatting
        self.mkdown = h2text.handle(html)

    def parse(self):
        TEXT_TAG = 'TEXT'
        HEADER_TAG = 'HEADER'
        LISTITEM_TAG = 'ITEM'
        ASSOCLI_TAG = 'ASSOCLI'

        # 传入的是element，即md的每行内容
        def getElementType(text):
            def isHeader(text):
                # 使用正则表达式匹配文本开头的井号字符来判断是否为标题行
                match = re.search(r'^#+\s+', text)
                # 如果匹配成功，则返回井号的数量；否则返回0
                return len([c for c in match.group(0) if c == '#']) if match else 0

            def isListItem(text):
                """
                判断给定文本是否为列表项。

                该函数通过检查文本是否以星号 '*' 开头来判断它是否为列表项。
                同时计算并返回缩进级别，这由匹配字符串中非星号字符数的一半决定，
                用于表示列表项的缩进层级。

                参数:
                text (str): 需要检查的文本字符串。

                返回:
                int: 如果文本是列表项，则返回缩进级别；否则返回 0。
                """
                # 使用正则表达式搜索文本开头是否为星号，允许前导空格
                match = re.search(r'^\s*\*', text)
                if match:
                    # 如果找到匹配，计算并返回缩进级别
                    return len([c for c in match.group(0) if c != '*']) / 2
                else:
                    # 如果没有找到匹配，返回0
                    return 0

            def isAssocListItem(text):
                # 此函数用于解析给定文本中的LISTITEM标签的depth属性值
                # 它通过正则表达式搜索LISTITEM标签，并返回其depth属性值（如果存在）作为整数
                # 如果没有depth属性或者文本中不存在LISTITEM标签，则返回0

                # 使用正则表达式匹配"&lt;LISTITEM"或"&lt;/LISTITEM"标签，可能包含depth属性
                # (?P<num>[0-9]+)命名捕获组，用于提取depth属性值（如果存在）
                match = re.search(r'&lt;[/]?LISTITEM(\sdepth="(?P<num>[0-9]+)")?&gt;', text)

                # 如果match对象不为空且能提取到num组，则返回num的整数值，否则返回0
                return int(match.group('num')) if match and match.group('num') is not None else 0

            #####################################
            hFlag = isHeader(text)
            if hFlag > 0:
                return (HEADER_TAG, hFlag)
            lFlag = isListItem(text)
            if lFlag > 0:
                return (LISTITEM_TAG, lFlag)
            alFlag = isAssocListItem(text)
            if alFlag > 0:
                return (ASSOCLI_TAG, alFlag)

            return (TEXT_TAG, 0)

        #####################################

        def stripHeader(text):
            """
            移除文本开头的井号(#)和后续的空格。

            对给定的文本，使用正则表达式移除开头的一个或多个井号(#)以及其后的空格，以便统一文本格式。

            参数:
            - text: 需要处理的文本字符串

            返回值:
            - 返回处理后的文本字符串
            """
            return re.sub(r'^#+\s+', '', text)

        def stripListItemTags(text):
            """
            移除文本中的LISTITEM标签。

            该函数使用正则表达式来查找并移除名为LISTITEM的HTML标签。
            它可以处理带有可选深度属性的LISTITEM标签，无论是否存在该属性都将移除标签。

            参数:
            text (str): 包含LISTITEM标签的文本。

            返回:
            str: 移除LISTITEM标签后的文本。
            """
            return re.sub(r'&lt;[/]?LISTITEM(\sdepth="[0-9]+")?&gt;', '', text)

        def stripListItemChar(text):
            """
            移除列表项前的特定字符。

            该函数使用正则表达式来移除字符串前的特定字符序列，具体来说是星号(*)及其前后的空格。
            这在处理列表项时特别有用，例如从文本文件中读取列表并希望移除格式字符时。

            参数:
            text (str): 需要进行字符移除操作的字符串。

            返回:
            str: 移除特定字符后的字符串。
            """
            # 使用正则表达式替换列表项前的特定字符
            return re.sub(r'^\s*\*\s*', '', text)

        def sentenceEndsWithColon(text):
            # pdb.set_trace()
            return stripListItemTags(text.strip()).endswith(':')

        def appendToDoc(outputDoc, text):
            # 获取element的类型
            etype = getElementType(text)[0]
            if etype == HEADER_TAG:
                appendToDoc(outputDoc, stripHeader(text))
            elif etype in [LISTITEM_TAG, ASSOCLI_TAG] or re.search('^\s*\*', text):
                appendToDoc(outputDoc, stripListItemChar(stripListItemTags(text)))
            else:
                outputDoc.append(text)

        #####################################
        def getNextPar(pars, index):
            while index < len(pars):
                if len(pars[index].strip()) > 0:
                    break
                index += 1
            return index

        def nextParIsListItem(pars, index, depth=-1):
            # 获得下一个非空元素的下标
            index = getNextPar(pars, index + 1)
            if index >= len(pars):
                return False

            eType, eDepth = getElementType(pars[index])
            return depth == -1 or eDepth > depth if eType in [LISTITEM_TAG, ASSOCLI_TAG] else False

        def uncapitalize(text):
            return text[:1].lower() + text[1:] if text else ''

        # TODO more complex processing to handle "the following information etc/..."
        def handleListItemText(prependText, listItemText):
            if prependText is None:
                return stripHeader(stripListItemChar(stripListItemTags(listItemText)))

            prependText = re.sub(r'\s*:\s*$', '',
                                 prependText) if 'following' not in prependText.lower() else prependText
            text = uncapitalize(stripHeader(stripListItemChar(stripListItemTags(listItemText))))
            # print(text)
            return ' '.join([prependText, text])

        #####################################
        # Returns a list of items instead?
        def handleList(outputDoc, pars, index, prependText):
            index = getNextPar(pars, index + 1)
            listDepth = -1
            # Get rest of list
            while index < len(pars):
                element = pars[index]
                if len(element.strip()) == 0:  # If blank line ignore...
                    appendToDoc(outputDoc, element)
                    index += 1
                    continue

                eType, eDepth = getElementType(element)
                if listDepth == -1:  # Set item depth if not already set
                    listDepth = eDepth

                # If not a list item or text associated with a list item and depth is incorrect.
                if eType not in [LISTITEM_TAG, ASSOCLI_TAG] or eDepth != listDepth:
                    index -= 1
                    break

                if sentenceEndsWithColon(handleListItemText(None, element)) and nextParIsListItem(mkdownPars, index,
                                                                                                  listDepth):
                    # pdb.set_trace()
                    index = handleList(outputDoc, pars, index, handleListItemText(prependText, element))
                    continue
                if eType == ASSOCLI_TAG:  # TODO Check why None was passed as first param
                    appendToDoc(outputDoc, handleListItemText(prependText, element))
                else:
                    appendToDoc(outputDoc, handleListItemText(prependText, element))
                index += 1
            return index

        # Hande plaintext multi-line lists. Either must start with same initial token (e.g., To ...), increasing number/enumeration, or end with semi-colon or "; and"
        def handlePlaintextMultilineList(outputDoc, pars, index, prependText):
            def getFirstTok(text):
                if text is None or len(text.strip()) == 0:
                    return None
                splitStr = text.strip().split(' ')
                return splitStr[0] if len(splitStr) >= 1 else None

            def containsLettersOrNumbers(text):
                """
                检查文本是否包含字母或数字。

                参数:
                text (str): 需要检查的文本。

                返回:
                bool: 如果文本中至少包含一个字母或数字，则返回True，否则返回False。
                """
                return bool(re.search(r'\w', text))

            def escapeCharsForRegex(tok):
                tok = re.sub(r'\(', '\\(', tok)
                tok = re.sub(r'\*', '\\*', tok)
                return re.sub(r'\)', '\\)', tok)

            def stripPlaintextListFormatters(text):
                text = re.sub('^\s*(\*|\-|\+|\\\-|\\\+|\u2022|\u00B7|\u2013|>)\s*', ' ', text, re.UNICODE)
                text = re.sub(r'^\s*([0-9][0-9]?\.)+[0-9][0-9]?\s*', ' ', text)
                text = re.sub(r'^\s*(\(([0-9][0-9]?|[A-Za-z])\)|([0-9][0-9]?|[A-Za-z])(\)|\.|\\\.))\s*', ' ', text)
                text = re.sub(r';(\s+(and|or))?\s*$', '; ', text, re.IGNORECASE)
                return text

            def combineText(prependText, appendText):
                ptext = re.sub(r'\s*:\s*$', '', stripPlaintextListFormatters(
                    prependText.strip())) if 'following' not in prependText.lower() else stripPlaintextListFormatters(
                    prependText.strip())
                etext = uncapitalize(stripPlaintextListFormatters(appendText.strip()))
                return ' '.join([ptext, etext])

            def checkLIType(text, expectedToken=None):
                defaultFResult = (False, None, False)  # matchFound, nextExpectedToken, isNextItemLast
                if text.startswith('#') or not containsLettersOrNumbers(
                        text):  # This is a header. Headers can't be list items...
                    return defaultFResult

                # Match this first if this was our pattern before...
                if expectedToken == ';' and re.search(r';(\s+(and|or))?\s*$', text, re.IGNORECASE):
                    return (True, ';',
                            bool(re.search(r';\s+(and|or)\s*$', text, re.IGNORECASE)))  # All items must with with ;

                # Matches *, \\-, \\+, and common unicode bulletpoints (\u2022, \u00B7)
                sresult = re.search('^\s*(\*|\-|\+|\\\-|\\\+|\u2022|\u00B7|\u2013|>)\s*', text, re.UNICODE)
                if sresult:
                    tok = sresult.group(0).strip()
                    if expectedToken is not None and expectedToken != tok:
                        return defaultFResult
                    return (True, tok, False)

                # Max match is double digits. Highly unlikely they have a list with over 100 items.
                # Matches X.Y.Z
                sresult = re.search(r'^\s*([0-9][0-9]?\.)+[0-9][0-9]?\s*', text)
                if sresult:
                    tok = sresult.group(0).strip()
                    if expectedToken is not None and expectedToken != tok:
                        return defaultFResult
                    # Increment
                    splt = tok.strip().split('.')
                    splt[-1] = str(str(int(splt[-1]) + 1))
                    return (True, '.'.join(splt), False)

                # Match roman numerals
                # Matches (x), x), x., x\., where x is a roman numeral between 1-99
                sresult = re.search(
                    r'^\s*(\(\s*(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX|XXI|XXII|XXIII|XXIV|XXV|XXVI|XXVII|XXVIII|XXIX|XXX|XXXI|XXXII|XXXIII|XXXIV|XXXV|XXXVI|XXXVII|XXXVIII|XXXIX|XL|XLI|XLII|XLIII|XLIV|XLV|XLVI|XLVII|XLVIII|XLIX|L|LI|LII|LIII|LIV|LV|LVI|LVII|LVIII|LIX|LX|LXI|LXII|LXIII|LXIV|LXV|LXVI|LXVII|LXVIII|LXIX|LXX|LXXI|LXXII|LXXIII|LXXIV|LXXV|LXXVI|LXXVII|LXXVIII|LXXIX|LXXX|LXXXI|LXXXII|LXXXIII|LXXXIV|LXXXV|LXXXVI|LXXXVII|LXXXVIII|LXXXIX|XC|XCI|XCII|XCIII|XCIV|XCV|XCVI|XCVII|XCVIII|XCIX)\s*\)|(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX|XXI|XXII|XXIII|XXIV|XXV|XXVI|XXVII|XXVIII|XXIX|XXX|XXXI|XXXII|XXXIII|XXXIV|XXXV|XXXVI|XXXVII|XXXVIII|XXXIX|XL|XLI|XLII|XLIII|XLIV|XLV|XLVI|XLVII|XLVIII|XLIX|L|LI|LII|LIII|LIV|LV|LVI|LVII|LVIII|LIX|LX|LXI|LXII|LXIII|LXIV|LXV|LXVI|LXVII|LXVIII|LXIX|LXX|LXXI|LXXII|LXXIII|LXXIV|LXXV|LXXVI|LXXVII|LXXVIII|LXXIX|LXXX|LXXXI|LXXXII|LXXXIII|LXXXIV|LXXXV|LXXXVI|LXXXVII|LXXXVIII|LXXXIX|XC|XCI|XCII|XCIII|XCIV|XCV|XCVI|XCVII|XCVIII|XCIX)(\s*\)|(\\)?\.))\s*',
                    text, flags=re.IGNORECASE)
                if sresult:
                    tok = sresult.group(0).strip()
                    if expectedToken is not None and expectedToken != tok:
                        return defaultFResult
                    res = re.sub(r'[IiVvXxLlCc]+', incrementListItemCallbackRoman, tok)
                    return (True, res, False)

                # Max match is double digits. Highly unlikely they have a list with over 100 items.
                # Matches (x), x), x., x\., where 0 <= x <= 99 or A <= x <= Z
                sresult = re.search(r'^\s*(\(\s*([0-9][0-9]?|[A-Za-z])\s*\)|([0-9][0-9]?|[A-Za-z])(\s*\)|(\\)?\.))\s*',
                                    text)
                if sresult:
                    tok = sresult.group(0).strip()
                    if expectedToken is not None and expectedToken != tok:
                        return defaultFResult
                    res = re.sub(r'[0-9A-Za-z]+', incrementListItemCallback, tok)
                    return (True, res, False)

                # Matches end of string ; AND/OR
                sresult = re.search(r';(\s+(and|or))?\s*$', text, re.IGNORECASE)
                if sresult:
                    if expectedToken is not None and expectedToken != ';':
                        return defaultFResult
                    return (
                        True, ';', re.search(r';\s+(and|or)\s*$', text, re.IGNORECASE))  # All items must with with ;

                # All words must start with same first token (e.g., We may send your data: To ..., To ...,)
                tok = getFirstTok(text).strip()
                if expectedToken is not None and expectedToken != tok:
                    return defaultFResult
                return (True, tok, False)

            ##################
            index = getNextPar(pars, index + 1)  # 获取需要链接的下一个段落下标
            nextTok = None
            breakNextItem = False
            modifiedDoc = False
            while index < len(pars):
                element = pars[index]  # 通过下标获取需要链接的文本内容
                if len(element.strip()) == 0:  # 忽略空白行
                    index += 1
                    continue

                eType, eDepth = getElementType(element)  # 获得需要链接段落的类型和深度
                if eType == HEADER_TAG:
                    index -= 1
                    break
                elif eType == LISTITEM_TAG:
                    nindex = handleList(outputDoc, pars, index - 1, prependText)
                    if nindex != index:
                        modifiedDoc = True
                    index = nindex
                    break

                # Get first character
                cont, nextTok, breakNextLine = checkLIType(element, nextTok)

                # Do not append, reverse index, and return...
                if not cont:
                    index -= 1
                    break

                nText = combineText(prependText, element)
                if sentenceEndsWithColon(element):
                    # pdb.set_trace()
                    nindex = handlePlaintextMultilineList(outputDoc, pars, index, nText)
                    if nindex != index:
                        modifiedDoc = True
                        index = nindex
                    else:  # CHECKME
                        appendToDoc(outputDoc, nText)
                        index += 1
                else:
                    modifiedDoc = True
                    appendToDoc(outputDoc, nText)
                    index += 1

                if breakNextItem:
                    break
                breakNextItem = breakNextLine

            if not modifiedDoc:
                appendToDoc(outputDoc, re.sub(r'\s*:\s*$', '', stripPlaintextListFormatters(prependText.strip())))
            return index

        def processMarkdown(outputDoc, pars, index=0, prependText=None):
            # Ensures that it is not a title heuristics ( > 2 tokens and all caps)
            def ensureNotTitle(text):
                """
                判断给定的文本是否为非标题格式。

                标题格式通常定义为：只有首词大写，其余单词小写（除非是专有名词）。
                本函数通过检查文本中大写开头的单词数量来判断文本是否为非标题格式。
                如果大写开头的单词数量少于总单词数的一定比例，则认为文本不是标题格式。

                参数:
                text -- 要检查的文本字符串

                返回:
                bool -- 如果文本不是标题格式，则返回True；否则返回False
                """
                # 移除文本两端的空白字符，检查是否为空
                if len(text.strip()) == 0:
                    return False

                # 计算非小写开头的单词数量，排除一些常见的介词和冠词
                ncap = [1 if t[0].isupper() else 0 for t in text.strip().split(' ') if
                        len(t) > 0 and t not in ['a', 'an', 'the', 'and', 'but', 'for', 'on', 'to', 'at',
                                                 'by', 'from', 'in', 'into', 'like', 'of', 'near', 'off',
                                                 'onto', 'out', 'over', 'past', 'up', 'upon', 'with', 'within',
                                                 'without']]

                # 如果文本中非小写开头的单词数量超过两个，且小写开头的单词数量不等于总单词数，则认为文本不是标题格式
                return len(ncap) > 2 and sum(ncap) < len(ncap)

            ######################################################
            while index < len(pars):
                element = pars[index]
                if len(element.strip()) == 0:
                    appendToDoc(outputDoc, element)
                    index += 1
                    continue

                eType, eDepth = getElementType(element)
                # if "Whenever there is a UK Data Transfer, your use of UK Data is subject to your compliance with the Approved Addendum (which is hereby incorporated by reference into these Terms and is deemed to have been entered into and completed as set out below)." in element:
                #     print(element)
                #     pdb.set_trace()

                # if stripListItemTags(element).strip().endswith(':'):
                #     element = stripListItemTags(element).strip()
                if eType == TEXT_TAG or stripListItemTags(element).strip().endswith(':'):
                    element = stripListItemTags(element).strip()
                    if sentenceEndsWithColon(element):
                        # pdb.set_trace()
                        if nextParIsListItem(mkdownPars, index):  # We have a div list items
                            index = handleList(outputDoc, pars, index, element)
                        elif ensureNotTitle(element):  # We have a plaintext list then...

                            index = handlePlaintextMultilineList(outputDoc, pars, index, element)
                        else:
                            appendToDoc(outputDoc, re.sub(r':\s*$', '.', element))
                    else:
                        appendToDoc(outputDoc, stripListItemTags(element))
                elif eType == HEADER_TAG:
                    # If element is anything other than TEXT_TAG, strip!
                    appendToDoc(outputDoc, stripHeader(element))
                elif eType in [LISTITEM_TAG, ASSOCLI_TAG]:
                    # print eType, eDepth
                    appendToDoc(outputDoc, stripListItemChar(stripListItemTags(element)))
                index += 1

        #####################################
        output = []
        mkdownPars = self.mkdown.split('\n')
        # print(mkdownPars)
        # with open('./tmp/tmp1.md', 'w', encoding='utf-8') as fwrite:
        #     fwrite.write(self.mkdown)
        processMarkdown(output, mkdownPars, 0)
        # print(output)
        # with open('./tmp/tmp1.txt', 'w', encoding='utf-8') as fwrite:
        #     for line in output:
        #         fwrite.write(line)
        #         fwrite.write('\n')
        return TextPostProcessor(output).postProcess()


#####################################

def main(filename):
    hprocessor = Preprocessor(filename)
    return hprocessor.parse()


def getOutputFilename(filename, outputDir):
    return os.path.join(outputDir, '{}.txt'.format(os.path.splitext(os.path.basename(filename))[0]))


def processFile(filename, outputDir=None):
    try:
        outputfilename = '{}.txt'.format(os.path.splitext(os.path.basename(filename))[0])
        if os.path.isfile(outputfilename):
            return

        if outputDir is not None:
            outputfilename = os.path.join(outputDir, outputfilename)
            res = main(filename)
            with codecs.open(outputfilename, 'w', 'utf-8') as outputfile:
                outputfile.write('\n'.join(uni.normalize(res)))
    except NonEnglishException:
        with codecs.open('nonenglish_apks.log', 'a', 'utf-8') as logfile:
            logfile.write(filename)
            logfile.write('\n')
        print('Error: \"{}\" is not English'.format(filename))


def processDirectory(directory, outputDir=None):
    for root, dirs, files in os.walk(directory):
        for f in files:
            print(os.path.join(root, f))
            processFile(os.path.join(root, f), outputDir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', help='Filename or directory containing html privacy policies. ')
    outputdir = "./plaintexts/"
    args = parser.parse_args()
    name = f"./htmls/{args.name}.html"
    if args.name is not None:
        if os.path.isfile(name):
            processFile(name, outputdir)
        elif os.path.exists(args.name):
            processDirectory(args.name, outputdir)
        else:
            print('Could not find \"{}\"'.format(args.name))
            sys.exit(1)
    else:
        parser.print_help(sys.stderr)
        sys.exit(1)
