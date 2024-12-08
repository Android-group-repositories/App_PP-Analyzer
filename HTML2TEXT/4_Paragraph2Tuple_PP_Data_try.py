import json
import logging
import time
import argparse

from pathlib import Path
from openai import OpenAI

client = OpenAI(
    api_key="sk-JFzKW5uHCHaEoEtKB7B3B7655562495d8c5f734fBb478cF8",
    base_url="https://api.holdai.top/v1"
)

# client = OpenAI(
#     api_key="sk-OLyeRhsjqDHg4UswihhmswfWrX37FHRssvQNiy6HdlFtt2zi",
#     base_url="https://api.moonshot.cn/v1",
# )

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

                Please excerpt sentences from the privacy policy summary that relate to data manipulation, taking care to use the original text as much as possible, not omitting references to data types and related manipulation, keeping the original contextual semantics of the excerpted sentences and replacing pronouns with the original words to ensure that the original meaning of the sentence is intact, and adapting the data types to the data flow to ensure that the meaning of the original text is appropriately adapted.
                
                Please be careful not to over-associate sentences, you need to ensure that the extracted sentences match the meaning expressed in the original text!!!

                As shown in the example below:


                example1:
                \"\"\"
                If you decide to create a user account on Instabridge, we will request certain information from you, which may include your username, password, email address, and profile picture. In the event that you choose to log in using your credentials from a third-party app (such as Facebook or Google), you give us permission to obtain your authentication information, such as your username, email address, and encrypted access credentials. Additionally, we may gather other information that is accessible through your third-party app account, such as your profile picture, country and hometown, date of birth, gender, and networks.

                We collect, store and use your personal information including your username and email address and information about how you use and access the Service because it is necessary in order to provide the Service requested by you pursuant to the contract made between you and us. If you do not provide us with this information we will not be able to provide you with the Service.
                \"\"\"

                Don't omit all data types, related operations, and source and destination of data types in the original text, and be sure to keep the original meaning!!!
                Subjects and operations can be converted appropriately, try to shift the subject to words that mean something like we, and the corresponding verbs need to be scratched and replaced, e.g. 'you provide' to 'we receive'

                Output in the following form


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
                history.pop()

    elif str(mode) == "2":
        sentences = []
        with open(f'./Sentences/{name}.txt', 'r', encoding='utf-8') as fread:
            for line in fread:
                sentences.append(line.strip('\n'))

        # history.pop()
        with open(f'./Tuples/{name}.csv', 'w', encoding='utf-8') as file:

            prompt2 = """
            I will give you a sentence about manipulating data types that may contain elements defined in the following tuple, which is filled with 'none' if there are no relevant elements, taking care to distinguish between each of the elements:
    
            <
                Subject of data manipulation; 
                Specific types of operations; 
                Data types; 
                More specific data types; 
                Source or destination of data type; 
                Conditions for data manipulation; 
                Purpose of data manipulation
            >
            There should be 7 elements present!!!
    
            Subject of data manipulation: Note the distinction between the subject being the developer or other, generally 'we' in a privacy policy means the developer.
            Specific types of operations: General operations can be divided into four categories: collect, share, use, and store, and if they do not belong to these four categories then replace them with 'none'.
            Data types: If there is a hypernym, use the hypernym.
            More specific data types: If data type is a hypernym, use example of the data type(Note that this is not an explanation of the hypernym), if no example, use 'none'.
            Source or destination of data type: Where data types come from or go to.
            Conditions for data manipulation: When operate on data types.
            Purpose of data manipulation: Why operate on data types.
    
            If there are multiple elements of a tuple that are connected using 'and' or 'or', they are separated by ','.
    
            Note the distinction between different data directions for collection and sharing, and watch out for verbs in passive voice, which can affect the flow of data and need to be converted!!!!
            
            Always make sure that the content of the elements in the tuple matches the definition of the meta ancestor, if there is no relevant content use 'none' to fill it in, but don't omit the original message!!!!
    
            Here are four examples, make sure that both the number of elements and the element content of the output tuple match the definition above, and no extra elements or none, not extract redundant elements, as well as making sure that the position of the elements matches the definition in the tuple, and that they are not in the wrong place!!!
            
            Just output the tuple as results!!!

    
            Input1:
            \"\"\"
            We use your Lenovo ID or Motorola ID and related registration and account information to identify you, including when you use certain of our software applications and our interactive services.
            \"\"\"
    
            Output1:
            <We; use; information; Lenovo ID, Motorola ID, related registration information, account information; from user; when use the software application, when use the interactive service; identify user>
    
    
            Input2:
            \"\"\"
            We may collect  your personal information (such as name, social security number, email address) and share with business partners as necessary to conduct business and complete transactions.
            \"\"\"
    
            Output2:
            <We; collect; personal information; name, social security number, email address; from user; none; conduct business and complete transaction>
            <We; share; personal information; name, social security number, email address; with business partners; none; conduct business and complete transaction>
    
            Input3:
            \"\"\"
            Your personal information (such as name, Social Security number, email address) will be shared with business partners as necessary to conduct business and complete transactions.
            \"\"\"
    
            Output3:
            <We; share; personal information; name, social security number, email address; with business partners; none; conduct business and complete transaction>
            
            Input4:
            \"\"\"
            We may use your device IP address to collect information about your general location.
            \"\"\"
            
            Output4:
            <We; use; device IP address; none; from device; none; collect location information>
            
            """

            history.append({
                "role": "system",
                "content": prompt2,
            })

            for s in sentences:
                file.write(
                    chat(f"\"\"\"{s}\"\"\"", history) + '\n')

            history.pop()
            # time.sleep(10)

    else:
        sentences = []
        with open(f'./Sentences/{name}.txt', 'r', encoding='utf-8') as fread:
            for line in fread:
                sentences.append(line.strip('\n'))


def main():
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--Name", help="Name")
    parser.add_argument("-m", "--Mode", help="Mode")
    args = parser.parse_args()

    name = Path(args.Name)
    mode = Path(args.Mode)
    convert(name, mode)


if __name__ == '__main__':
    main()
