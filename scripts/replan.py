# -*- coding: utf-8 -*-
"""
重写 index.html 的编排段。

节奏（用户要求）：
  "卡片快落地时应该播放视频，让注意力从飞入转移到视频；
   视频播放完之后再飞入下一个卡片。"

实现：视频起播时刻 = 落定时刻 − 0.20s（"快落地时"），
      于是卡片停稳的瞬间视频已经在动，视线自然交棒。
      视频播完 + 短暂呼吸，下一条才升入。
"""
import io
import json
import re

P = r"D:\cut\token-mg\index.html"
s = io.open(P, encoding="utf-8").read()

REAL = {1: 0.533, 2: 0.567, 3: 1.000, 4: 0.833, 5: 4.233}
LEAD = 0.55
RISE, OVER, PRESS = 0.62, 0.26, 0.09
LAND = RISE + OVER + PRESS          # 0.97
PREROLL = 0.20                      # 提前起播量（"快落地时"）
BREATH = 0.45                       # 播完后的呼吸
HOLD = 1.05
ZOOM = 1.05

LAY = [
    ("s1", [ 634, 318], 0.87, -8.5, 1),
    ("s2", [1272, 352], 0.85,  6.8, 2),
    ("s3", [ 682, 728], 0.89,  5.2, 3),
    ("s4", [1238, 744], 0.86, -6.4, 4),
    ("s5", [ 960, 540], 0.90,  0.0, 5),
]


def plan():
    cues, lands, starts = {}, {}, {}
    t = LEAD
    for i in range(1, 6):
        cues[i] = round(t, 3)
        lands[i] = round(t + LAND, 3)
        starts[i] = round(t + LAND - PREROLL, 3)   # 快落地时起播
        end = lands[i] + REAL[i] + BREATH
        t = end
    hero_land = lands[5]
    zoom_at = round(hero_land + HOLD, 3)
    zoom_end = round(zoom_at + ZOOM, 3)
    # 压轴要播完；放大结束后仍保留残余播放
    total = round(max(zoom_end, hero_land + REAL[5]) + 0.30, 3)
    return cues, lands, starts, zoom_at, zoom_end, total


def main():
    cues, lands, starts, zoom_at, zoom_end, total = plan()

    print("第N条  升入     起播     落定     播放     "
          "落定后剩余")
    for i in range(1, 6):
        print("  %d   %6.2f  %6.2f  %6.2f   %.3f    %.3f"
              % (i, cues[i], starts[i], lands[i], REAL[i],
                 lands[i] + REAL[i] - lands[i]))
    print("\n压轴放大 %.2f -> %.2f   全片 %.3fs" % (zoom_at, zoom_end, total))

    # ── 生成 LAY 代码块 ──────────────────────────────────
    items = []
    for sid, at, sc, rot, n in LAY:
        items.append('          { id: "%s", at: [%d, %d], s: %s, rot: %s, cue: %s, land: %s }'
                     % (sid, at[0], at[1], sc, rot, cues[n], lands[n]))
    lay_js = ("        var LAY = [\n" + ",\n".join(items) + "\n        ];\n"
              "        var ZOOM_AT = %s, ZOOM_END = %s, TOTAL = %s;\n"
              % (zoom_at, zoom_end, total))

    # ── 替换 LAY / HERO / 时间常量段 ─────────────────────
    start = s.index("        // ── 节拍")
    end = s.index("        var tl = gsap.timeline")
    s2 = s[:start] + lay_js + "\n" + s[end:]

    # ── 替换 Root duration ───────────────────────────────
    s2 = re.sub(r'data-duration="[\d.]+">', 'data-duration="%s">' % total, s2, count=1)

    # ── 替换视频的 data-start / data-duration ────────────
    for i in range(1, 6):
        st = starts[i]
        # 该条需要播放到全片结束
        du = round(total - st, 3)
        s2 = re.sub(r'<video id="v%d" data-start="[\d.]+" data-duration="[\d.]+"'
                    % i,
                    '<video id="v%d" data-start="%s" data-duration="%s"' % (i, st, du),
                    s2, count=1)

    io.open(P, "w", encoding="utf-8").write(s2)

    # ── 输出音频计划（供下一步写 audio 标签）────────────
    audioplan = {"voice": [], "sfx": []}
    for i in range(1, 6):
        audioplan["voice"].append({"id": "a%d" % i, "start": starts[i], "dur": REAL[i]})
    for sid, at, sc, rot, n in LAY:
        audioplan["sfx"].append({"id": "x-s%d" % n, "start": round(cues[n] + 0.02, 3)})
    audioplan["sfx"].append({"id": "x-zoom", "start": zoom_at})
    io.open(r"D:\cut\token-mg\scripts\audioplan.json", "w", encoding="utf-8").write(
        json.dumps(audioplan, ensure_ascii=False, indent=2))

    print("\nindex.html 编排段已重写；audioplan.json 已写出")


if __name__ == "__main__":
    main()
