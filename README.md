# mortis

> Mortis 就像是看了 10000 次 MyGO 的群友，后面忘了。

## 生成台词集合

参考 mygo-gen.py（需要安装 pysub2），对应的字幕组仓库是 <https://github.com/Nekomoekissaten-SUB/Nekomoekissaten-Storage>。需要注意的是，该字幕的 license 是 CC BY-NC-ND 4.0，这意味着脚本生成的文件（以及对应的 embedding）无法共享，需要自己动手操作。

也可以自己收集去重，每行一句即可。

## 回复生成方法

三种参考方法：

- m1：把整个台词集全塞到 prompt 里面，让模型选择（4k 行台词大约 40k token，按每 1M token 2 元来算的话，100 块可以推理个大约 1250 次，有点小贵）
- m2：分两步，第一步让模型提供适合回复的关键词，搜索后第二步让模型选择
- m3：分两阶段，第一阶段生成每一句台词的 embedding 保存到本地，第二阶段让模型输出回复，回复也生成 embedding，选择最相似的回复（容易前言不搭后语）
