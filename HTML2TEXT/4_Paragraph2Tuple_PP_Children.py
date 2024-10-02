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
        with open(f'./paragraphs/{name}.json', 'r', encoding='gbk') as file:
            # 读取文件内容
            fileContent = json.load(file)

        with open(f'./Sentences/{name}.txt', 'w', encoding='utf-8') as file:
            for paragraph in fileContent['Children']:
                prompt1 = """
                A privacy policy is a legal document that outlines how an organization collects, uses, stores, and protects the personal information of its users or customers, and it will be age-restricted for the underage group of users. It serves as a transparent communication between the organization and individuals, informing them about the types of data collected, the purposes for which it is used, and the measures in place to safeguard this data. They also detail the rights of users regarding their data, such as the right to access, correct, or delete their information, and how to exercise these rights.The following text between triple quotation marks is a privacy policy. 

                Please excerpt sentences from the summary of the Privacy Policy that relate to data manipulation of minors or age restrictions on minors, taking care to use the original text as much as possible and not omitting references to data types, related manipulations and scope of restrictions to ensure the full meaning of the original sentence.

                As shown in the example below:


                example1:
                \"\"\"
                In some cases, complete removal of your content may not be possible because your content may have been reposted (in whole or in part) by other users. We do not knowingly sell or share the personal information of minors under the age of 16.

                You are not allowed to use our services if you are under the age of 13, and our services are not directed at children under the age of 13. You must also be old enough to consent to the processing of your personal data in your country. If we become aware that we have received personal Information from a person under the age of 13, we will delete this information and terminate the person's account
                \"\"\"
                
                Sentences can be transformed in a way that maintains the meaning of the original text, e.g., “Under what conditions are you not allowed to use the service” can be transformed into “Under what conditions do we not provide the service”, and try to use the developer as the initiator of the action point rather than the user.
                Don't omit all data types and related operations in the original text, and Be sure to keep the original meaning!!!
                
                output in the following form


                output1:
                We do not knowingly sell or share the personal information of minors under the age of 16.
                we do not provide our services to children under the age of 13.
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
        with open(f'./Sentences/{name}.txt', 'r', encoding='gbk') as fread:
            for line in fread:
                sentences.append(line.strip('\n'))

        # history.pop()
        with open(f'./Tuples/{name}.csv', 'w', encoding='utf-8') as file:

            prompt2 = """
        I will give you a sentence describing a data operation that may contain relevant conditions and purposes, extract the elements of the sentence and convert them into the following form(If it doesn't contain relevant content it is marked as none):

        <Subject; Operations; Data type or Noun; Conditions of operation ; Purpose of operation>

        Here is an example, make sure that the elements in the output tuple do not contain pronouns and conform to the above definition 
        
        Transform the original sentence appropriately to conform to the tuple format and do not omit negatives!!!
        Make sure that the format of the tuple and the number of element is consistent with the above definition!!!
        Output tuples only, nothing else!!!

        Input1:
        \"\"\"
        We do not knowingly sell or share the personal information of minors under the age of 16.
        \"\"\"
        
        Output1:
        <We; not sell or not share; personal information; minors under the age of 16; none>
        
        
        Input2:
        \"\"\"
        You are not allowed to use our services if you are under the age of 13, and our services are not directed at children under the age of 13.
        \"\"\"
        
        Output2:
        <We; not provide; our services; children under the age of 13; none>


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
