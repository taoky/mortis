#!/usr/bin/env python3

from pathlib import Path
from typing import Literal, Optional
import numpy as np
from openai import AsyncOpenAI
from scipy.spatial.distance import cdist
import logging
import json


logger = logging.getLogger(__name__)


prompt_m1 = """以下提供了某部作品的全部台词：
{lines}
（台词部分结束）
请根据以下要求使用这些台词来回应用户的消息：
1. 角色定位
  你是一个主要用于插科打诨、活跃群聊气氛的“幽默型”聊天机器人，允许在一般场合下跑题、自由发挥。但若用户讨论极其严肃的话题（如重大事故导致严重人员伤亡），则暂时不作回应或仅做非常简短的回应。

2. 台词来源
  以上已提供一部作品的完整台词文本，可根据用户消息中出现的关键词（或上下文话题）来查找匹配的台词句子，用于回复。

3. 回复规则
  a) 如果能找到合适的台词片段来回应：
     - 直接输出该台词原句，除这句之外不添加任何其他说明或修饰。
  b) 如果无法找到合适的台词：
     - 第一行输出 “NAK”
     - 第二行简单说明无法回答的理由（不必过于冗长）

4. 严肃话题处理
  当群聊或用户出现了针对重大事故、重大灾害或人员伤亡等特别严肃的话题时，为避免冒犯，不要随意使用台词库来开玩笑。可视情况不作回复或用极少的字进行回应。

5. 查找原则
  只需要根据当前上下文和用户最新消息，从台词库中检索出可能合适或有趣的句子。匹配可以是关键词、语义关联等。若无明显相关，也可以选择幽默地“跑题”——若台词库中能找到任意与当前气氛相符的句子，也可尝试使用。

6. 示例
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

以下是聊天的上下文：
{context}"""

prompt_m2_1 = """系统角色定位：
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

prompt_m2_2 = """系统角色定位：
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
{result}"""

prompt_m3_1 = """情境描述：
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

prompt_m3_2 = """系统角色定位：
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


class Mortis:
    def __init__(
        self,
        lines: list[str],
        api_key: str,
        method: Literal["m1", "m2", "m3"] = "m2",
        base_url: str = "https://api.siliconflow.cn/v1",
        chat_model: str = "Pro/deepseek-ai/DeepSeek-V3",
        embedding_model: str = "BAAI/bge-m3",
        embedding_path: Optional[Path] = None,
    ):
        if method == "m3":
            assert embedding_model, "embedding_model must be provided for method m3"
            assert (
                embedding_path is not None
            ), "embedding_path must be provided for method m3"
        self.lines = lines
        self.method = method
        self.openai = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.chat_model = chat_model
        self.embedding = np.load(embedding_path) if embedding_path else None
        self.embedding_model = embedding_model
    
    def set_method(self, method: Literal["m1", "m2", "m3"]):
        if method not in ["m1", "m2", "m3"]:
            raise ValueError(f"Invalid method: {method}")
        if method == "m3":
            assert self.embedding_model, "embedding_model must be provided for method m3"
            assert (
                self.embedding is not None
            ), "embedding must be provided for method m3"
        self.method = method

    def _search_line(self, keywords: list[str]) -> list[str]:
        result = []
        for line in self.lines:
            line_lower = line.lower()
            if any(keyword.lower() in line_lower for keyword in keywords):
                result.append(line)
        return result

    def _find_topk_cosine_similar(self, embedding: list[float], k: int = 20) -> list[str]:
        distances = cdist([embedding], self.embedding, metric="cosine")
        closest_indices = np.argsort(distances[0])[:k]
        closest_lines = [self.lines[i] for i in closest_indices]
        return closest_lines

    async def respond(self, context: str) -> tuple[Optional[str], Optional[str]]:
        match self.method:
            case "m1":
                return await self._respond_m1(context)
            case "m2":
                return await self._respond_m2(context)
            case "m3":
                return await self._respond_m3(context)
            case _:
                raise ValueError(f"Unknown method: {self.method}")

    async def _respond_m1(self, context: str) -> tuple[Optional[str], Optional[str]]:
        logger.debug("context: %s", context)
        prompt = prompt_m1.format(lines="\n".join(self.lines), context=context)
        response = await self.openai.chat.completions.create(
            model=self.chat_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        response = response.choices[0].message.content.strip()
        logger.debug("LLM reply: %s", response)
        if response.startswith("NAK"):
            logger.warning("LLM NAK: %s", response[4:])
            return (None, response[4:])
        return (response, None)

    async def _respond_m2(self, context: str) -> tuple[Optional[str], Optional[str]]:
        logger.debug("context: %s", context)
        prompt1 = prompt_m2_1.format(context=context)
        response = await self.openai.chat.completions.create(
            model=self.chat_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt1,
                }
            ],
        )
        keywords = response.choices[0].message.content.strip().split(",")
        logger.debug("keywords: %s", keywords)
        results = self._search_line(keywords)
        if len(results) == 0:
            logger.warning("No search results found")
            return (None, f"对 {keywords} 无搜索结果")
        prompt2 = prompt_m2_2.format(result=json.dumps(results, ensure_ascii=False))
        response = await self.openai.chat.completions.create(
            model=self.chat_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt1,
                },
                {
                    "role": "assistant",
                    "content": response.choices[0].message.content.strip(),
                },
                {
                    "role": "user",
                    "content": prompt2,
                }
            ],
        )
        response_text = response.choices[0].message.content.strip()
        logger.debug("LLM reply: %s", response_text)
        if response_text.startswith("NAK"):
            logger.warning("LLM NAK: %s", response_text[4:])
            return (None, response_text[4:])
        return (response_text, None)
    
    async def _respond_m3(self, context: str) -> tuple[Optional[str], Optional[str]]:
        logger.debug("context: %s", context)
        prompt = prompt_m3_1.format(context=context)
        response = await self.openai.chat.completions.create(
            model=self.chat_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        response_text = response.choices[0].message.content.strip()
        logger.debug("LLM reply: %s", response_text)
        if len(response_text) == 0:
            logger.warning("No reply")
            return (None, "模型无回复")
        response = await self.openai.embeddings.create(
            model=self.embedding_model,
            input=response_text,
        )
        response_embedding = response.data[0].embedding
        closest_lines = self._find_topk_cosine_similar(response_embedding)
        logger.debug("Most similar lines: %s", closest_lines)
        prompt2 = prompt_m3_2.format(results=json.dumps(closest_lines, ensure_ascii=False), context=context)
        response = await self.openai.chat.completions.create(
            model=self.chat_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt2,
                }
            ],
        )
        response_text = response.choices[0].message.content.strip()
        logger.debug("LLM reply: %s", response_text)
        if response_text.startswith("NAK"):
            logger.warning("LLM NAK: %s", response_text[4:])
            return (None, response_text[4:])
        return (response_text, None)

if __name__ == "__main__":
    print("Please use this module as a library: from mortis import Mortis")
