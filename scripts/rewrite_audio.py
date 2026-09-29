# -*- coding: utf-8 -*-
"""
重写 index.html 的音频段：用规整的数字、单引号包属性、内部用双引号。
单引号包 JSON 是合法的 HTML，且避免了 &quot; 转义噪音。
"""
import io
import json
import re

P = r"D:\cut\token-mg\index.html"
s = io.open(P, encoding="utf-8").read()

SQ = chr(39)


def lane(points):
    """points: [(t, v), ...] -> data-automation 属性文本"""
    obj = {"version": 1,
           "lanes": [{"target": "volume",
                      "points": [{"t": round(float(t), 3), "v": round(float(v), 3)}
                                 for t, v in points]}]}
    txt = json.dumps(obj, separators=(",", ":"))
    return "data-automation=" + SQ + txt + SQ


# ── 原声：按各卡落定时刻进轨，50ms 淡入 / 80ms 淡出 ────────
VOICE = [
    # id, 起, 时长
    ("a1", 1.590, 0.534),
    ("a2", 2.090, 0.580),
    ("a3", 2.500, 1.021),
    ("a4", 2.870, 0.836),
    ("a5", 3.920, 4.249),
]
# ── SFX：逐拍钉帧（判例 S2）───────────────────────────────
SFX = [
    # id, 文件, 起, 时长, 峰值, 淡入, 淡出
    ("x-rise",  "riser-cine.mp3",          0.000, 4.600, 0.30, 0.60, 0.60),
    ("x-s1",    "swoosh-quick.mp3",        0.600, 0.781, 0.34, 0.03, 0.08),
    ("x-s2",    "swoosh-quick.mp3",        1.100, 0.781, 0.32, 0.03, 0.08),
    ("x-s3",    "swoosh-quick.mp3",        1.550, 0.781, 0.30, 0.03, 0.08),
    ("x-s4",    "swoosh-quick.mp3",        1.960, 0.781, 0.28, 0.03, 0.08),
    ("x-hero",  "air-woosh-quick.mp3",     2.580, 1.511, 0.40, 0.04, 0.12),
    ("x-hit",   "impact-zoom-quick.mp3",   3.900, 1.222, 0.42, 0.03, 0.20),
    ("x-drop",  "hit-weak.mp3",            3.450, 0.591, 0.22, 0.02, 0.10),
    ("x-open",  "air-whoosh-powerful.mp3", 5.050, 1.839, 0.42, 0.05, 0.30),
    ("x-glint", "sparkle-touch.mp3",       5.600, 2.333, 0.26, 0.06, 0.40),
]

lines = []
lines.append("      <!-- 原声：视频 muted，声音走独立 audio；按各卡落定时刻进轨 -->")
for i, st, du in VOICE:
    pts = [(0, 0), (0.05, 1.0), (max(0.06, du - 0.08), 1.0), (du, 0)]
    lines.append(
        '      <audio id="%s" data-start="%.3f" data-duration="%.3f" src="assets/voice/%s.m4a"\n'
        "             %s></audio>" % (i, st, du, i[1], lane(pts)))

lines.append("")
lines.append("      <!-- SFX：逐拍钉帧（判例 S2）—— 每条注明对应动作 -->")
for i, f, st, du, pk, fi, fo in SFX:
    pts = [(0, 0), (fi, pk), (max(fi + 0.01, du - fo), pk), (du, 0)]
    lines.append(
        '      <audio id="%s" data-start="%.3f" data-duration="%.3f" src="assets/sfx/%s"\n'
        "             %s></audio>" % (i, st, du, f, lane(pts)))

block = "\n".join(lines) + "\n"

# 用新块替换：从第一个 audio 到最后一个 audio 结束
start = s.index("\n      <audio")
end = s.rindex("></audio>") + len("></audio>")
s2 = s[:start] + "\n" + block + s[end + 1:]

io.open(P, "w", encoding="utf-8").write(s2)

# 校验
ok = bad = 0
for m in re.finditer(r'id="([^"]+)"\s+data-start="[^"]*"\s+data-duration="[^"]*"\s+src="[^"]*"\s*'
                     + SQ + r'(\{[^' + SQ + r']*\})' + SQ, s2, re.S):
    try:
        json.loads(m.group(2))
        ok += 1
    except Exception as e:
        bad += 1
        print("  x %s: %s" % (m.group(1), e))
print("音频元素 %d 条，合法 %d，非法 %d" % (ok + bad, ok, bad))
