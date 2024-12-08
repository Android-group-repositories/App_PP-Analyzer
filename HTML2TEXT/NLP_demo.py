import spacy

# 加载英文模型
nlp = spacy.load("en_core_web_sm")

# 待分析的句子
sentence = "The quick brown fox jumps over the lazy dog."

# 处理句子
doc = nlp(sentence)

# 输出每个词的词性
for token in doc:
    print(f"{token.text}: {token.pos_}")
