# -*- coding: utf-8 -*-
"""
重写 index.html 的音频段。

用户要求：
- "声音小" -> 已用 normalize_audio.py 归一到 -15 LUFS（当前 assets/voice/*.m4a）
- "不需要加入额外音效（后缀之后再加入）" -> 本版移除全部 SFX，只留原声

保留极简的淡入淡出，避免起止爆音。
"""
import io
import json
import re

P = r"D:\cut\token-mg\index.html"
s = io.open(P, encoding="utf-8").read()
plan = json.load(io.open(r"D:\cut\token-mg\scripts\audioplan.json", encoding="utf-8"))

SQ = chr(39)


def lane(points):
    obj = {"version": 1,
           "lanes": [{"target": "volume",
                      "points": [{"t": round(float(t), 3), "v": round(float(v), 3)}
                                 for t, v in points]}]}
    return "data-automation=" + SQ + json.dumps(obj, separators=(",", ":")) + SQ


lines = ["      <!-- 原声：已归一到 -15 LUFS / 真峰值 <=-1.4 dBTP；视频 muted，声音走独立 audio -->"]
for v in plan["voice"]:
    i, st, du = v["id"], v["start"], v["dur"]
    fi = 0.04
    fo = max(fi + 0.02, du - 0.07)
    lines.append(
        '      <audio id="%s" data-start="%.3f" data-duration="%.3f" src="assets/voice/%s.m4a"\n'
        "             %s></audio>" % (i, st, du, i[1], lane([(0, 0), (fi, 1.0), (fo, 1.0), (du, 0)])))

block = "\n".join(lines) + "\n"

# 替换：从第一个 audio 到最后一个 audio
start = s.index("\n      <audio")
end = s.rindex("></audio>") + len("></audio>")
s2 = s[:start] + "\n" + block + s[end + 1:]

# 清掉遗留的 SFX 注释行
s2 = re.sub(r"\n\s*<!--\s*SFX[^>]*-->\n", "\n", s2)
s2 = re.sub(r"\n\s*<!--\s*原声：[^>]*-->\n", "\n", s2)

io.open(P, "w", encoding="utf-8").write(s2)

# 校验
from html.parser import HTMLParser
import json as J


class V(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.bad = []
        self.ok = 0

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "data-automation" in d:
            try:
                J.loads(d["data-automation"])
                self.ok += 1
            except Exception as e:
                self.bad.append((d.get("id"), str(e)))


p = V()
p.feed(io.open(P, encoding="utf-8").read())
print("音频元素 automation：合法 %d，非法 %d" % (p.ok, len(p.bad)))
for i, e in p.bad:
    print("  x", i, e)
print("SFX 是否已清空:", "assets/sfx" not in io.open(P, encoding="utf-8").read())
