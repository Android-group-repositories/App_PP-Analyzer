import json
import logging
import time
import argparse

from pathlib import Path
from openai import OpenAI

client = OpenAI(
    api_key="your api key",
    base_url="https://api.moonshot.cn/v1",
)

# 我们定义一个全局变量 messages，用于记录我们和 Kimi 大模型产生的历史对话消息
# 在 messages 中，既包含我们向 Kimi 大模型提出的问题（role=user），也包括 Kimi 大模型给我们的回复（role=assistant）
# 当然，也包括初始的 System Prompt（role=system）
# messages 中的消息按时间顺序从小到大排列
history = [
    {
        "role":
        "system",
        "content":
        "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"
    },
]


def chat(input, history):
    """
    chat 函数支持多轮对话，每次调用 chat 函数与 Kimi 大模型对话时，
    Kimi 大模型都会”看到“此前已经产生的历史对话消息，换句话说，Kimi 大模型拥有记忆。
    """

    # 我们将用户最新的问题构造成一个 message（role=user），并添加到 messages 的尾部
    history.append({
        "role": "user",
        "content": input,
    })

    # 携带 messages 与 Kimi 大模型对话
    completion = client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=history,
        temperature=0,
    )
    # 通过 API 我们获得了 Kimi 大模型给予我们的回复消息（role=assistant）
    assistant_message = completion.choices[0].message

    history.pop()

    # 为了让 Kimi 大模型拥有完整的记忆，我们必须将 Kimi 大模型返回给我们的消息也添加到 messages 中
    # history.append(assistant_message)

    return assistant_message.content


def convert(name, mode=1):
    if str(mode) == "1":
        # 打开文件，确保文件路径正确
        with open(f'./paragraphs/{name}.json', 'r', encoding='utf-8') as file:
            # 读取文件内容
            fileContent = json.load(file)

        with open(f'./Sentences/{name}.txt', 'w', encoding='utf-8') as file:
            for paragraph in fileContent['Data']:
                prompt1 = """
                A privacy policy is a legal document that outlines how an organization collects, uses, stores, and protects the personal information of its users or customers. It serves as a transparent communication between the organization and individuals, informing them about the types of data collected, the purposes for which it is used, and the measures in place to safeguard this data. They also detail the rights of users regarding their data, such as the right to access, correct, or delete their information, and how to exercise these rights.The following text between triple quotation marks is a privacy policy. 
                
                Please excerpt sentences from the privacy policy summary that relate to data manipulation, taking care to use the original text wherever possible, and not omitting references to data types and related manipulations to ensure that the meaning of the original sentence is complete, and adjust the data type according to the flow of data to ensure that the meaning of the original text is appropriately adjusted.
                
                As shown in the example below:
                
                
                example1:
                \"\"\"
                If you decide to create a user account on Instabridge, we will request certain information from you, which may include your username, password, email address, and profile picture. In the event that you choose to log in using your credentials from a third-party app (such as Facebook or Google), you give us permission to obtain your authentication information, such as your username, email address, and encrypted access credentials. Additionally, we may gather other information that is accessible through your third-party app account, such as your profile picture, country and hometown, date of birth, gender, and networks.
                
                We collect, store and use your personal information including your username and email address and information about how you use and access the Service because it is necessary in order to provide the Service requested by you pursuant to the contract made between you and us. If you do not provide us with this information we will not be able to provide you with the Service.
                \"\"\"
                
                Don't omit all data types and related operations in the original text, and Be sure to keep the original meaning!!!
                Convert all inclusive relations to the form "such as", associate Hypernym with Hyponym using "such as" for each converted sentence whenever possible, and enclose the inclusive relations with (), and output them in the following form
                
                
                output1:
                We request certain information (such as username, password, email address and profile picture) from you if you create a user account on Instabridge.
                We obtain authentication information (such as username, email address, encrypted access credentials) from third-party app (such as Facebook, Google) if you log in using your credentials from third-party app.
                We gather other information (such as profile picture, country and hometown, date of birth, gender, networks) through third-party app account.
                We collect, store and use personal information (such as username, email address) in order to provide the Service.
                """

                history.append({
                    "role": "system",
                    "content": prompt1,
                })

                file.write(chat("\"\"\"" + paragraph + "\"\"\"", history))
                file.write('\n')
                # time.sleep(60)
                # print(history)
                history.pop()
                # print(history)
                # print('-' * 50)

    else:
        sentences = []
        with open(f'./Sentences/{name}.txt', 'r', encoding='utf-8') as fread:
            for line in fread:
                sentences.append(line.strip('\n'))

        # history.pop()
        with open(f'./Tuples/{name}.csv', 'w', encoding='utf-8') as file:

            prompt2 = """
        I will give you a sentence describing a data operation that may contain relevant conditions and purposes, extract the elements of the sentence and convert them into the following form(If it doesn't contain relevant content it is marked as none):
        
        <Subject of data manipulation; Specific types of operations; Data types; Conditions for data manipulation; Purpose of data manipulation>
        
        Here is an example, make sure that the elements in the output tuple do not contain pronouns and conform to the above definition 
        
        Make sure that the format of the tuple and the number of element is consistent with the above definition!!!
        Output tuples only, nothing else!!!
        
        Input1:
        \"\"\"
        We collect personal information such as first name, last name, phone number, postal address, email address, date of birth, and profile photo from you when you use the service.
        \"\"\"

        Output1:
        <We; collect; personal information; when use the service; none>


        Input2:
        \"\"\"
        We may share your personal information (such as name, Social Security number, email address, billing and delivery address, telephone number, payment information) with business partners as necessary to conduct business and complete transactions.
        \"\"\"

        Output2:
        <We; share; personal information; none; conduct business and complete transaction>
        
        
            """

            history.append({
                "role": "system",
                "content": prompt2,
            })

            for s in sentences:
                file.write(chat(f"\"\"\"{s}\"\"\"", history) + '\n')

            history.pop()
            # time.sleep(10)


def main():
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                        level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--Name", help="Name")
    parser.add_argument("-m", "--Mode", help="Mode")
    args = parser.parse_args()

    name = Path(args.Name)
    mode = Path(args.Mode)
    convert(name, mode)


if __name__ == '__main__':
    main()
