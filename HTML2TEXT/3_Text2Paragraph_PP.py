import json
import argparse
import logging
import pdb
import re
import time
import itertools

from pathlib import Path

nrestrictedPhrase = [
    "shall not", "may not", "should not", "must not", "agree", "restricted",
    "not allowed to", "prohibited", "forbidden to", "cannot",
    "not permitted to", "will not", "must refrain from",
    "not authorized to", "not to", "barred from",
    "ought not to", "disallowed from", "does not have permission to",
    "forbidden from", "not granted the right to",
    "will not be allowed to", "banned from",
    "compelled to avoid", "obliged to refrain from", "has no right to",
    "not capable of", "under no circumstances to", "unable to"
]

prestrictedPhrase = [
    "shall", "will", "is to", "is required to", "ought to", "be expected to", "would",
    "may", "might", "could", "is allowed to", "is permitted to",
    "should", "is advised to", "is recommended to", "is supposed to", "is expected to",
    "must", "have to", "need to", "are required to", "undertakes", "undertake", "agrees", "agree"
]

restrictedPhrase = [
    "agree", "restricted",
    "prohibited", "forbidden to", "cannot",
    "refrain from",
    "not authorized to", "not to", "barred from",
    "ought not to", "disallowed from", "does not have permission to",
    "forbidden from", "not granted the right to",
    "banned from",
    "compelled to avoid", "has no right to",
    "not capable of", "under no circumstances to", "unable to",
    "shall", "will", "required to", "ought to", "expected to", "would",
    "may", "might", "must", "could", "allowed to", "permitted to",
    "should", "advised to", "recommended to", "supposed to",
    "have to", "need to", "undertakes", "undertake"
]
# restrictedPhrase = [
#     "must"
# ]

# ppKeyWord = [
#     "privacy policy", "privacy policies", "privacy statement", "privacy statements", "privacy practices",
#     "privacy notice"
# ]

childKeyword = [
    "child", "infant", "toddler", "baby", "children",
    "kid", "kids",
    "youngster", "youngsters",
    "youth", "teenager", "teenagers", "adolescent", "young person", "youths",
    "minor", "underage person", "minors", "underage persons",
    "juvenile", "juveniles",
    "underage", "young",
    "young one", "young ones",
    "little one", "little ones", "small child", "small children",
    "pupil", "pupils", "student", "students", "schoolchild", "schoolchildren",
    "teen", "teens",
    "young adult", "young adults",
    "pre-adult", "pre-adults",
    "pubescent", "pubescents",
    "preteen", "preteens", "tween", "pre-adolescent", "preadolescents"
]

# dataItem_old = [
#     "SSN", "Social Security Number", "social security code", "national insurance number",
#     "Passport Number", "passport ID", "passport code", "travel document number",
#     "Driver's License Number", "driving license number", "driver ID", "DLN",
#     "email", "electronic mail",
#     "Postal Address", "mailing address", "street address", "home address",
#     "Person Name", "full name", "individual name", "personal name",
#     "Phone Number", "telephone number", "mobile number", "contact number",
#     "internet protocol address", "IP", "network address",
#     "Android ID", "Android identifier", "Android unique ID",
#     "Router SSID", "network name", "Wi-Fi name", "service set identifier",
#     "GSF ID", "Google Services Framework ID", "GSF identifier", "Google ID",
#     "Advertising ID", "ad ID", "advertising identifier", "marketing ID",
#     "cookie", "personal identifiers",
#     "MAC Address", "media access control address", "hardware address", "physical address",
#     "IMEI", "International Mobile Equipment Identity", "device ID", "mobile ID",
#     "SIM Serial Number", "SIM number", "SIM card ID", "ICCID",
#     "Serial Number", "product ID", "serial code",
#     "Gender", "sex",
#     "Race", "racial group", "racial identity", "ethnicity",
#     "ethnic group", "ethnic identity", "cultural background",
#     "Date of Birth", "birthdate", "DOB", "birth date",
#     "Age", "years", "contact address",
#     "Voiceprint", "voice recognition", "voice ID", "vocal pattern",
#     "Fingerprint", "biometric ID", "dactyloscopy",
#     "Geolocation", "GPS location", "geographic location",
#     "Browsing History", "web history", "internet history", "online activity",
#     "Search History", "search log", "search queries", "browsing behavior",
#     "login credential", "credentials", "access token", "secret key",
#     "Device Identifiers", "information", "data"
# ]

datas = [
    "prohibited data",
    "restricted information",
    "services data",
    "user information",
    "prohibited information",
    # "personal data",
    "account information",
    "device identifier",
    "personal identifier",
    "government identifier",
    "software identifier",
    "hardware identifier",
    "contact information",
    "personal information",
    "device information",
    "biometric information",
    "user information",
    "phone number",
    "passport number",
    "license number",
    "serial number",
    "ip address",
    "email address",
    "postal address",
    "mac address",
    "person name",
    "android id",
    "gsf id",
    "advertising id",
    "router ssid",
    "imei",
    "gender",
    "race",
    "ethnicity",
    "geolocation",
    "voiceprint",
    "fingerprint",
    "search history",
    "browsing history",
    # "cookie",
    "login credential",
    "token"
]

dataItem = [
    "SSN",
    "DLN",
    "email", "mail",
    "IP", "name",
    "identifier", "id", "identifiers", "number", "code", "address",
    "SSID", "identity", "history",
    "cookie",
    "IMEI",
    "ICCID",
    "Gender", "sex",
    "Race", "ethnicity",
    "group", "background",
    "birthdate",
    "Age", "years",
    "Voiceprint", "recognition", "pattern",
    "Fingerprint", "dactyloscopy",
    "location",
    "activity",
    "log", "queries", "behavior",
    "credential", "credentials", "token", "key",
    "information", "data"
]

d_verb = [
    "share", "store", "utilize", "collect", "transmit", "process", "storage", "processing", "use", "request", "receive"
]

# p_verb = [
#     "abide", "post", "provide", "disclose", "disclosure", "publish", "make available", "maintain", "have",
#     "made available", "disclosing", "describes", "describe"
# ]

a_noun = [

]

# developer = [
#     "customer", "you", "member", "members", "developers", "developer", "users", "user", "publisher", "company",
#     "licensee"
# ]

developer = [
    "we"
]

fs_pattern = r'[^.]*'

developer_lower = {s.lower() for s in developer}
d_verb_lower = {s.lower() for s in d_verb}
# b_verb_lower = {s.lower() for s in p_verb}
dataItem_lower = {s.lower() for s in datas}


def keywordRecognize1(keyword1, keyword2, keyword3, line, flag, result):
    item = []
    for kw1 in keyword1:
        for kw2 in keyword2:
            for kw3 in keyword3:
                pattern1 = rf'{kw1}\b{fs_pattern}\b{kw2}\b{fs_pattern}\b{kw3}'
                match = re.search(pattern1, line.lower())
                if match:
                    item.append(kw1 + ' ' + kw2 + ' ' + kw3)

    if len(item) != 0:
        dataItems = ",".join(list(set(item)))
        if dataItems in result[flag]:
            if line not in result[flag][dataItems]:
                result[flag][dataItems].append(line)
        else:
            result[flag][dataItems] = []
            result[flag][dataItems].append(line)


def keywordRecognize2(keyword1, keyword2, line, flag, result):
    if re.search(
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+([1-9]|[12][0-9]|3[01]),\s+(\d{4})'.lower(),
            line.lower()):
        return
    if re.search(r'definitions'.lower(), line.lower()):
        return
    item = []
    for kw1 in keyword1:
        for kw2 in keyword2:
            pattern1 = kw1.lower() + r'[^.,:]*' + kw2.lower() + r'[\s:]'

            if re.search(pattern1, line.lower()):
                item.append(kw1.lower() + ' ' + kw2.lower())
    if len(item) != 0:
        dataItems = ",".join(list(set(item)))
        if dataItems in result[flag]:
            if line not in result[flag][dataItems]:
                result[flag][dataItems].append(line)
        else:
            result[flag][dataItems] = []
            result[flag][dataItems].append(line)


def keywordRecognize3(keyword1, line, flag, result):
    item = []

    for kw1 in keyword1:
        pattern1 = rf'\s\b{kw1.lower()}[ .,:]'

        if re.search(pattern1, line.lower()):
            item.append(kw1.lower())

    pattern2 = r'\busers?\b[^\.]*?\b(under|over)\b[^\.]*?\d{2}'
    if re.search(pattern2, line.lower()):
        result[flag]["user under|over xx"].append(line)
    if len(item) != 0:
        dataItems = ",".join(list(set(item)))
        if dataItems in result[flag]:
            if line not in result[flag][dataItems]:
                result[flag][dataItems].append(line)
        else:
            result[flag][dataItems] = []
            result[flag][dataItems].append(line)


def keywordRecognize4(keyword1, keyword2, line, flag, result):
    item = []
    for kw1 in keyword1:
        for kw2 in keyword2:
            pattern1 = r'\b' + kw1.lower() + r'\b' + r'\s*[^.,:]*\s*' + \
                       r'\b' + kw2.lower() + r'\b' + r'[ .,:]'
            pattern2 = r'\b' + kw2.lower() + r'\b' + r'\s*[^.,:]*\s*' + \
                       r'\b' + kw1.lower() + r'\b' + r'[ .,:]'
            if re.search(pattern1, line.lower()):
                item.append(kw1.lower() + ' ' + kw2.lower())
            elif re.search(pattern2, line.lower()):
                item.append(kw2.lower() + ' ' + kw1.lower())

    if len(item) != 0:
        dataItems = ",".join(list(set(item)))

        if dataItems in result[flag]:
            if line not in result[flag][dataItems]:
                result[flag][dataItems].append(line)
        else:
            result[flag][dataItems] = []
            result[flag][dataItems].append(line)


def plural_to_singular(p, word):
    return p.singular_noun(word) or word


def extractParagraph(sdk_name, debugFlag):
    result = {}
    result['rp'] = []
    result['dk'] = {}
    result['ck'] = {}
    result['pk'] = {}
    result['ck']["user under|over xx"] = []

    with open(f'./plaintexts/{sdk_name}.txt', 'r', encoding='utf-8') as rfile:
        # 遍历每个段落
        for paragraph in rfile:

            # 记录段落中是否含有约束相关的词
            flag = 0
            # 存储每个段落识别到的词
            final_developers = []
            final_data_verbs = []
            final_data_nouns = []
            final_pp_verbs = []

            # 判断句子中是否有约束相关的词
            # if flag == 0:
            #     for rp in restrictedPhrase:
            #         for ms in developer:
            #             # pdb.set_trace()
            #             if re.search(rf'{ms}{fs_pattern}{rp}', paragraph.lower()):
            #                 flag = 1
            #                 break
            #         if flag != 0:
            #             break
            # if flag == 1:
            # 识别段落中形容开发者的词
            for d in developer:
                if re.search(rf'\b{d}', paragraph.lower()):
                    final_developers.append(d)
            # 识别段落中描述数据处理的词
            for d in d_verb:
                if re.search(rf'\b{d}', paragraph.lower()):
                    final_data_verbs.append(d)
            # 识别段落中形容数据的词
            for d in datas:
                if re.search(rf'\b{d}', paragraph.lower()):
                    final_data_nouns.append(d)
            # 识别段落中描述PP的词
            # for d in p_verb:
            #     if re.search(rf'\b{d}', paragraph.lower()):
            #         final_pp_verbs.append(d)
            result['rp'].append({
                'paragraph': paragraph,
                'developers': list(set(final_developers)),
                'data_verbs': list(final_data_verbs),
                'data_nouns': list(set(final_data_nouns)),
                # 'pp_verbs': list(final_pp_verbs)
            })
            # print(paragraph[:15])
            # print(final_developers)
            # print(final_data_verbs)
            # print(final_data_nouns)
            # # print(final_pp_verbs)
            # print('-' * 50)

    # 按照段落进行分类识别
    for p_dict in result['rp']:
        keywordRecognize1(p_dict['developers'], p_dict['data_verbs'],
                          p_dict['data_nouns'], p_dict['paragraph'], 'dk', result)
        # keywordRecognize4(p_dict['pp_verbs'], ppKeyWord,
        #                   p_dict['paragraph'], 'pk', result)
        keywordRecognize3(childKeyword, p_dict['paragraph'], 'ck', result)
        # result['ck']["user under|over xx"] = list(
        #     set(result['ck']["user under|over xx"]))

    # if len(result['ck']["user under|over xx"]) == 0:
    #     del result['ck']["user under|over xx"]

    if debugFlag:
        with open(f'./paragraphs/{sdk_name}_tmp.json', 'w', encoding='utf-8') as wfile:
            json.dump(result, wfile, ensure_ascii=False, indent=4)

    outputParagraph = {
        'Data': list(set(itertools.chain.from_iterable(result['dk'].values()))),
        'Children': list(set(itertools.chain.from_iterable(result['ck'].values()))),
        'PP': list(set(itertools.chain.from_iterable(result['pk'].values())))
    }

    with open(f'./paragraphs/{sdk_name}.json', 'w') as wfile:
        json.dump(outputParagraph, wfile, ensure_ascii=False)


def main():
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--sdkName", help="Sdk Name")
    parser.add_argument("-d", "--debug", help="Input tempData", action="store_true")
    args = parser.parse_args()

    sdk_name = Path(args.sdkName)
    debugFlag = args.debug
    extractParagraph(sdk_name, debugFlag)


if __name__ == "__main__":
    begin = time.time()
    main()
    end = time.time()
    logging.info(f"Extract Done! {end - begin}")
