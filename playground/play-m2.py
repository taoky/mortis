#!/usr/bin/env python3
# 使用模拟 Function Calling 的方法搜索台词并由 LLM 选择，分成两轮问答

from openai import OpenAI
import json

with open("key") as f:
    key = f.read().strip()
with open("mygo") as f:
    mygo = f.read().strip().split("\n")
with open("contexts/3") as f:
    context = f.read().strip()

client = OpenAI(api_key=key, base_url="https://api.siliconflow.cn/v1")
model = "Pro/deepseek-ai/DeepSeek-V3"


def search_line(keywords: list[str]) -> list[str]:
    result = []
    for line in mygo:
        line_lower = line.lower()
        if any(keyword.lower() in line_lower for keyword in keywords):
            result.append(line)
    return result


prompt1 = f"""系统角色定位：
1. 你是一个用于闲聊的聊天机器人，主要任务是在非严肃的群聊场合插科打诨、活跃气氛。
2. 在群聊内容并非重大人员伤亡或者极其严肃的话题时，可以略微“跑题”，表现幽默和娱乐性。

目标：
1. 当前阶段，你需要根据可用的对话上下文和所处情境，尽可能多地思考适合检索的关键词组合，并输出它们。
2. 每组关键词之间使用英文逗号（,）分隔，在一行全部输出。
3. 关键词需要尽可能简短，台词只会在包含其中某个关键词的时候才会被检索到。
4. 不要做任何额外解释或输出；此阶段仅需输出关键词列表，用于后续由用户调用搜索函数获取台词。 

以下是聊天的上下文：
{context}
"""

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": prompt1,
        }
    ],
)

response_text = response.choices[0].message.content
print(response_text)
results = search_line(response_text)
print("搜索结果：", results)

if len(results) > 0:
    prompt2 = f"""系统角色定位：
1. 你依旧是用于群聊闲聊的机器人，负责幽默有趣地回复用户。
2. 若话题涉及特别严肃的事件（如重大伤亡），需要保持谨慎和严肃，不做娱乐化处理。

目标：
1. 你已经从用户处得到了搜索函数返回的台词列表（JSON 数组）。
2. 你只能从这些台词中选出最合适、幽默的内容来回复，或在无合适台词时声明无法回答。
3. 禁止再次发起搜索请求。

回复格式：
1. 如果可以从返回的台词中选到合适台词，请直接输出台词内容进行回答。
2. 如果搜索结果不满足需求，或无法从中找到可用台词，请：
— 第一行回复“NAK”
— 第二行简要说明原因（可保持幽默或简练）。
示例：
NAK
没有可用的台词了

下面是一些 Bot 使用台词库回复的示例：
── 示例 1 ──
User：你复习下周的考试了吗？
Bot：并没有
── 示例 2 ──
User：我不想申请PhD了，想跑路
Bot：跑了
── 示例 3 ──
User：woc，这么多人？
Bot：好多观众啊

注意：
1. 在非严肃话题中，尽量保持幽默、活泼的风格。
2. 不允许再进行任何新的搜索请求，必须基于现有搜索结果进行回答或报告无法回答。
3. 只有在无可用台词时，才使用“NAK”。

以下是搜索函数返回的台词列表（JSON 数组）：
{json.dumps(results, ensure_ascii=False)}"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt1,
            },
            {
                "role": "assistant",
                "content": response_text,
            },
            {
                "role": "user",
                "content": prompt2,
            }
        ],
    )
    print(response.choices[0].message.content)
else:
    print("没有任何匹配。")
