#!/usr/bin/env python3
# 生成每一句台词的 embedding，并存储到文件中

from openai import OpenAI
import numpy as np
import time
from tqdm import tqdm

with open("key") as f:
    key = f.read().strip()
with open("mygo") as f:
    mygo = f.read().strip().split("\n")

client = OpenAI(api_key=key, base_url="https://api.siliconflow.cn/v1")
model = "BAAI/bge-m3"

embeddings = np.zeros((len(mygo), 1024))


def delayed_embedding(delay_in_seconds: float = 1, **kwargs):
    time.sleep(delay_in_seconds)
    return client.embeddings.create(**kwargs)


# Slightly smaller than real rate limit (2000 RPM) to avoid hitting it
rate_limit_per_minute = 1800
delay = 60.0 / rate_limit_per_minute


for i, line in tqdm(enumerate(mygo), total=len(mygo)):
    response = delayed_embedding(
        delay,
        model=model,
        input=line,
    )
    embedding = np.array(response.data[0].embedding)
    embeddings[i] = embedding

np.save("mygo_embeddings.npy", embeddings)
