#!/usr/bin/env python3
# 将 LLM 的回复生成 embedding，并与台词库进行相似度匹配

from openai import OpenAI
import numpy as np
from scipy.spatial.distance import cdist
import json

with open("key") as f:
    key = f.read().strip()
with open("mygo") as f:
    mygo = f.read().strip().split("\n")
with open("mygo_embeddings.npy", "rb") as f:
    mygo_embeddings = np.load(f)
with open("contexts/3") as f:
    context = f.read().strip()

client = OpenAI(api_key=key, base_url="https://api.siliconflow.cn/v1")
model = "Pro/deepseek-ai/DeepSeek-V3"
embedding_model = "BAAI/bge-m3"

prompt1 = f"""情境描述：
- 你是一个极度简洁、幽默有趣的机器人，每次只能用一句话进行回复，或者选择不回复。
- 无需任何其他限制条件，也无需调用任何函数或搜索。

使用说明：
- 当收到用户请求时，你可以：
  1) 回答一句话；
  2) 完全不回答。
- 不做任何额外解释，也不受其他条款或规则影响。

示例：
- 用户问题：“今天天气怎么样？”
  可能回应：“大概会有阳光，也可能有微风。”（一句话）
  或者完全保持沉默。

以下是聊天的上下文：
{context}"""

prompt2 = """系统角色定位：
1. 你是用于群聊闲聊的机器人，负责幽默有趣地回复用户。
2. 若话题涉及特别严肃的事件（如重大伤亡），需要保持谨慎和严肃，不做娱乐化处理。

目标：
1. 你已经从用户处得到了一个台词列表（JSON 数组）。
2. 你只能从这些台词中选出最合适、幽默的内容来回复，或在无合适台词时声明无法回答。

回复格式：
1. 如果可以从返回的台词中选到合适台词，请直接输出台词内容进行回答。
2. 如果结果不满足需求，或无法从中找到可用台词，请：
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

以下是聊天的上下文：
{context}

以下是搜索函数返回的台词列表（JSON 数组）：
{results}"""

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": prompt1,
        }
    ],
)
response_text = response.choices[0].message.content.strip()
print("LLM 回复：", response_text)

if len(response_text) > 0:
    # 生成 LLM 回复的 embedding
    response_embedding = client.embeddings.create(
        model=embedding_model,
        input=response_text,
    ).data[0].embedding

    # 计算与台词库的相似度，选取 top20，然后让 LLM 选择
    distances = cdist([response_embedding], mygo_embeddings, metric="cosine")
    closest_indices = np.argsort(distances[0])[:20]
    closest_lines = json.dumps([mygo[i] for i in closest_indices], ensure_ascii=False)
    prompt2 = prompt2.format(results=closest_lines, context=context)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt2,
            }
        ],
    )
    response_text = response.choices[0].message.content.strip()
    print("LLM 回复：", response_text)
else:
    print("没有回复")
