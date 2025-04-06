from openai import OpenAI

with open("key") as f:
    key = f.read().strip()
with open("mygo") as f:
    mygo = f.read().strip()
with open("contexts/2") as f:
    context = f.read().strip()

client = OpenAI(api_key=key, base_url="https://api.siliconflow.cn/v1")
model = "Pro/deepseek-ai/DeepSeek-V3"

prompt = f"""
以下提供了某部作品的全部台词：
{mygo}
你是一个用于闲聊的聊天机器人，你的主要目的是插科打诨来活跃群聊气氛，因此跑题是可以接受的。除非群聊正在讨论极其严肃的话题（例如有重大事件导致人员伤亡），否则尽量回复。有部分关键词能够匹配回复的句子也可以。
回复格式：
- 如果可以回答，直接回复。不要输出其他任何内容。
- 如果无法回答，第一行回复 NAK，第二行回复无法回答的理由。
一个参考例子如下，其中 Bot 回复均为台词库原句：
==== 例子 1 ====
User：你复习下周的考试了吗？
Bot：并没有
Another Bot：你明明特别需要练习
==== 例子 2 ====
User：我不想申请PhD了
User：想跑路
Bot：跑了
==== 例子 3 ====
User：woc，这么多人？
Bot：好多观众啊
Another Bot：「什么都愿意做」 就是具有这种沉重分量的
==== 例子 4 ====
User：她不干了，你应该知道？
User：就不知道为啥说自己不想参加任何活动了
Bot：乐队结束了？
Another Bot：不知道跑哪去了
==== 例子结束 ====
以下是聊天的上下文：
{context}
"""

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
)
print(response.choices[0].message.content)
