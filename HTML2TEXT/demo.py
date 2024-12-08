import spacy
from spacy.matcher import DependencyMatcher

# 初始化模型和匹配器
nlp = spacy.load('en_core_web_sm')
matcher = DependencyMatcher(nlp.vocab)

# 定义一个匹配模式
pattern = [
    {"RIGHT_ID": "verb", "RIGHT_ATTRS": {"LEMMA": "like", "POS": "VERB"}},
    {"LEFT_ID": "verb", "REL_OP": ">", "RIGHT_ID": "subject", "RIGHT_ATTRS": {"DEP": "nsubj"}}
]

matcher.add("LIKE_SUBJECT", [pattern])

# 测试文本
doc = nlp("I like apples.")

# 查找匹配
matches = matcher(doc)
print(matches)
