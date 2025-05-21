import pysubs2
import glob
import os
import re
from collections import defaultdict

words = defaultdict(set)
FILENAME_REGEX = re.compile(r"MyGO!!!!! \[(\d\d)\]")

SKIPS = [
    "m 0",
    "~~",
    "→",
    "本字幕由",
    re.compile(r"「[　　　  　　　]+」"),
    "注：",
]
REPLACEMENTS = {
    "公司让我不能跟家人之外\\N的人说，但我无论如何都\\N想告诉你": "公司让我不能跟家人之外的人说，但我无论如何都想告诉你",
    "　纷纷雪　": "「纷纷雪」",
    "　印影散散　": "「印影散散」",
    "　短篇集 寿喜烧": "「短篇集 寿喜烧」",
    "当我注意到自己心中\\N涌出的感情时，已经完全被带着走\\N了，不知为何咬紧了牙握紧了拳头，\\N甚至哭了起来。": "当我注意到自己心中涌出的感情时，已经完全被带着走了，不知为何咬紧了牙握紧了拳头，甚至哭了起来。",
    "虽然我还有些没整理好情绪，但这个\\N乐队真的很神奇。等我冷静了再写感\\N想。": "虽然我还有些没整理好情绪，但这个乐队真的很神奇。等我冷静了再写感想。",
    "我以为会一团糟，到结束却觉得\\N感动？兴奋？": "我以为会一团糟，到结束却觉得感动？兴奋？",
    "今天的Live真精彩。乐队叫\\NCRYCHIC。吉他、键盘还有鼓都\\N不错，贝斯也挺熟练，挺有好感的。": "今天的Live真精彩。乐队叫CRYCHIC。吉他、键盘还有鼓都不错，贝斯也挺熟练，挺有好感的。",
}

for i in glob.glob("Nekomoekissaten-Storage/BanG_Dream/MyGO/*.JPSC.ass"):
    filename = os.path.basename(i)
    matches = FILENAME_REGEX.search(filename)
    assert matches
    ep = matches.group(1)
    # subs = pysubs2.load(i)
    with open(i) as f:
        file_contents = f.read()
        for r in REPLACEMENTS:
            file_contents = file_contents.replace(r, REPLACEMENTS[r])
        subs = pysubs2.SSAFile.from_string(file_contents)
    for line in subs:
        if "JP" in line.style or line.style == "Default":
            continue
        text = line.plaintext
        is_skip = False
        for s in SKIPS:
            if type(s) is str and s in text or type(s) is re.Pattern and s.search(text):
                is_skip = True
                break
        if is_skip:
            continue
        parts = text.split("\n")
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if p.endswith("，") or p.endswith(","):
                p = p.rstrip("，,")
            if p.startswith("「") and "」" not in p:
                p = p.lstrip("「")
            words[p].add(ep)

# print(words)

with open("mygo.txt", "w") as f:
    for word in sorted(words):
        # for id in sorted(words[word]):
        #     print(id, end=";", file=f)
        print("", word, file=f)
