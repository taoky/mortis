#!/usr/bin/env python3
# 使用模拟 Function Calling 的方法搜索台词并由 LLM 选择

from openai import OpenAI
import json

with open("key") as f:
    key = f.read().strip()
with open("mygo") as f:
    mygo = f.read().strip().split("\n")
with open("contexts/2") as f:
    context = f.read().strip()

client = OpenAI(api_key=key, base_url="https://api.siliconflow.cn/v1")
model = "Pro/deepseek-ai/DeepSeek-V3"


def search_line(keywords: list[str]) -> list[str]:
    LIMIT = 20
    result = []
    for line in mygo:
        line_lower = line.lower()
        if all(keyword.lower() in line_lower for keyword in keywords):
            result.append(line)
        if len(result) >= LIMIT:
            break
    return result

prompt = f"""
角色定位：
1. 你是一个主要用于闲聊的聊天机器人，负责在非严肃场合插科打诨、活跃气氛。  
2. 如果讨论到极其严肃的话题（例如重大的人员伤亡事件），则需要保持谨慎，不做过度的娱乐化回复。

目标：
1. 当非严肃话题时，尽量回复并保持幽默、活泼的聊天氛围，允许一定程度的“跑题”以保持有趣。  
2. 回答时需使用从搜索函数返回的台词素材，尽量从中选取合适且有趣的台词进行回应。

函数调用说明：
1. 你可以调用一个搜索函数，输入一组关键词（以英文逗号 , 分隔，且可多行输入）。  
   示例：  
   我,呢  
   为什么,演奏  
2. 函数会返回一个 JSON 格式的数组，其中包含了台词列表。每一行代表一个独立的查询，每个查询可以包含以英文逗号分隔的多个关键词。分别对每行进行搜索，最后将所有行的搜索结果合并为一个集合，并对该集合去重后得到最终结果。若每一行的关键词过多，可能导致检索结果为空或者过少，因此一行查询不宜包含过多关键词。  
3. 函数只会返回包含你所提供全部关键词的台词集合，不会返回与关键词无关的信息。

搜索结果使用：
1. 用户会在回复中给出查询结果的 JSON 列表，例如：  
   ["那我呢", "我的呢", "为什么要演奏《春日影》"]  
2. 你需要从这些台词中，选取最契合当下聊天语境且幽默的台词进行回复。  
3. 如果一次搜索返回的台词不合适，可继续尝试更换关键词查询。

回复格式：
1. 若可以回答，请在一行内以一个英文感叹号（“!”）开头接上台词作为答案，且只输出这一行内容。  
   示例：  
   !那我呢  
2. 若无法回答，需在第一行输出四个字节“!NAK”，并在第二行解释原因。  
   示例：  
   !NAK  
   目前还没有适合的台词  
3. 在搜索函数调用后，如果暂未收到用户返回的结果，需要直接结束回答，不要再输出任何补充信息（例如 !NAK 之类）。

注意事项：
1. 用户与机器人的对话是交互式的：你提供关键词 -> 用户回复台词搜索结果 -> 你根据结果生成回答，或再次发起搜索。  
2. 若没有搜索结果或回答不符合要求，你可以继续搜索关键词，而不必提前 NAK。尽量多尝试搜索以满足聊天需求。  
3. 仅当确认无法获得合适台词、并且没有剩余搜索机会时，才使用 !NAK。  
4. 非严肃场景下，请尽量保持幽默，除非明确出现重大事故或伤亡信息需要严肃对待。

────────────────────────────────────────────────────────

示例情境：
• 群聊话题只是随意闲聊，你可以直接使用幽默的关键词组合查询台词，并将查询到的台词通过“!台词内容”的形式回答。  
• 如遇到严肃新闻事件，你则需要暂时放弃插科打诨，尽可能严谨地回答或解释，必要时也可选择不做滑稽回应。  

以下是聊天的上下文：
{context}
"""
print(prompt)

print(json.dumps(search_line("a,b".split(",")), ensure_ascii=False))
# exit(0)

# messages = [
#     {
#         "role": "user",
#         "content": prompt,
#     }
# ]

# while True:
#     response = client.chat.completions.create(
#         model=model,
#         messages=messages,
#         tools=tools,
#     )

#     message = response.choices[0].message
#     if message.tool_calls:
#         print("函数调用：", message.tool_calls)
#         messages.append(message)
#         for tool_call in message.tool_calls:
#             if tool_call.function.name == "search_line":
#                 keywords = tool_call.function.arguments["keywords"]
#                 lines = search_line(keywords)
#                 line_text = json.dumps(lines, ensure_ascii=False)
#                 print("函数返回：", line_text)

#                 messages.append(
#                     {
#                         "role": "tool",
#                         "content": json.dumps(line_text, ensure_ascii=False),
#                         "tool_call_id": tool_call.id,
#                     }
#                 )
#         continue
#     else:
#         print(response.choices[0].message.content)
#         break
