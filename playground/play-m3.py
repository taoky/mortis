#!/usr/bin/env python3
# 将 LLM 的回复生成 embedding，并与台词库进行相似度匹配

from openai import OpenAI
import numpy as np
from scipy.spatial.distance import cdist

with open("key") as f:
    key = f.read().strip()
with open("mygo") as f:
    mygo = f.read().strip().split("\n")
with open("mygo_embeddings.npy", "rb") as f:
    mygo_embeddings = np.load(f)
with open("contexts/1") as f:
    context = f.read().strip()

client = OpenAI(api_key=key, base_url="https://api.siliconflow.cn/v1")
model = "Pro/deepseek-ai/DeepSeek-V3"
embedding_model = "BAAI/bge-m3"

prompt = f"""情境描述：
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
{context} """

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": prompt,
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

    # 计算与台词库的相似度
    distances = cdist([response_embedding], mygo_embeddings, metric="cosine")
    closest_index = np.argmin(distances)
    closest_line = mygo[closest_index]

    print("最相似的台词：", closest_line)
else:
    print("没有回复")
