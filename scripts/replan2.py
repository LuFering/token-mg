# -*- coding: utf-8 -*-
"""
重新设计节奏，解决"黑框"问题。

问题：卡片从 t=cue 开始飞（0.62s）+ settle(0.26) + press(0.09)，
      而视频在 land-0.2s 才起播 -> 卡片出现后有 ~0.77s 窗口是纯黑。

用户要求的本意是"视线交棒"：卡片飞入时注意力在运动上，
快落地时视频开始动，注意力转向内容，播完再进下一张。

修正方案：
  - 视频起播 = cue + 0.30s（升入已过半，卡片已足够大、位置接近落点）
  - 升入缩短到 0.50s，使"飞行后段 + 落定"都有画面
  - 前四条视频很短（0.53~1.0s），播完后 HOLD 补足到"看得清"的时长
"""
import io
import json
import re

P = r"D:\cut\token-mg\index.html"
s = io.open(P, encoding="utf-8").read()

REAL = {1: 0.533, 2: 0.567, 3: 1.000, 4: 0.833, 5: 4.233}
LEAD = 0.50
RISE, OVER, PRESS = 0.50, 0.22, 0.08
LAND = RISE + OVER + PRESS           # 0.80
PREROLL = 0.30                       # 视频在升入 60% 处起播（cue+0.30）

# 每条从"落定"到"下一条开始升入"的停留
# = 视频剩余播放 + 呼吸。视频很短，所以补足到至少 MIN_SHOW 秒，让观众看清
MIN_SHOW = 1.30

HOLD = 1.20                          # 压轴停稳后停留
ZOOM = 1.05

LAY = [
    ("s1", [ 634, 318], 0.87, -8.5, 1),
    ("s2", [1272, 352], 0.85,  6.8, 2),
    ("s3", [ 682, 728], 0.89,  5.2, 3),
    ("s4", [1238, 744], 0.86, -6.4, 4),
    ("s5", [ 960, 540], 0.90,  0.0, 5),
]


def main():
    cues, lands, starts = {}, {}, {}
    t = LEAD
    for i in range(1, 6):
        cues[i] = round(t, 3)
        lands[i] = round(t + LAND, 3)
        starts[i] = round(t + PREROLL, 3)        # 升入 60% 处起播
        played = lands[i] - starts[i]            # 落定时已播了多久
        remain = max(0.0, REAL[i] - played)      # 落定后还要播多久
        # 落定后停留：至少 MIN_SHOW，且覆盖剩余播放
        hold = max(MIN_SHOW, remain + 0.30)
        t = lands[i] + hold
        print("  第%d条 cue=%5.2f 起播=%5.2f 落定=%5.2f 落定后停留=%.2f (视频余%.2f)"
              % (i, cues[i], starts[i], lands[i], hold, remain))

    hero_land = lands[5]
    zoom_at = round(hero_land + HOLD, 3)
    zoom_end = round(zoom_at + ZOOM, 3)
    total = round(max(zoom_end + 0.25, hero_land + REAL[5] + 0.25), 3)

    print("\n  压轴放大 %.2f -> %.2f   全片 %.3fs" % (zoom_at, zoom_end, total))

    # ── 写回 LAY 块 ─────────────────────────────────────
    items = []
    for sid, at, sc, rot, n in LAY:
        items.append('          { id: "%s", at: [%d, %d], s: %s, rot: %s, cue: %s, land: %s }'
                     % (sid, at[0], at[1], sc, rot, cues[n], lands[n]))
    block = ("        var LAY = [\n" + ",\n".join(items) + "\n        ];\n"
             "        var ZOOM_AT = %s, ZOOM_END = %s, TOTAL = %s;\n"
             % (zoom_at, zoom_end, total))
    s2 = re.sub(r"        var LAY = \[.*?var ZOOM_AT = [\d.]+, ZOOM_END = [\d.]+, TOTAL = [\d.]+;\n",
                block, s, count=1, flags=re.S)

    # ── 常量 ────────────────────────────────────────────
    s2 = re.sub(r"        var RISE = [\d.]+, OVER = [\d.]+, PRESS = [\d.]+;",
                "        var RISE = %s, OVER = %s, PRESS = %s;" % (RISE, OVER, PRESS),
                s2, count=1)
    s2 = re.sub(r"        var HOLD = [\d.]+, ZOOM = [\d.]+;",
                "        var HOLD = %s, ZOOM = %s;" % (HOLD, ZOOM), s2, count=1)

    # ── root duration ───────────────────────────────────
    s2 = re.sub(r'data-duration="[\d.]+">', 'data-duration="%s">' % total, s2, count=1)

    # ── 视频 data-start / data-duration ─────────────────
    for i in range(1, 6):
        st = starts[i]
        du = round(total - st, 3)
        s2 = re.sub(r'<video id="v%d" data-start="[\d.]+" data-duration="[\d.]+"' % i,
                    '<video id="v%d" data-start="%s" data-duration="%s"' % (i, st, du),
                    s2, count=1)

    # ── 音频 data-start / data-duration ─────────────────
    for i in range(1, 6):
        st, du = starts[i], REAL[i]
        s2 = re.sub(r'<audio id="a%d" data-start="[\d.]+" data-duration="[\d.]+"' % i,
                    '<audio id="a%d" data-start="%s" data-duration="%s"' % (i, st, du),
                    s2, count=1)

    s2 = s2.replace("XRISE", "RISE")   # 防御性
    io.open(P, "w", encoding="utf-8").write(s2)
    print("\nindex.html 已更新")


if __name__ == "__main__":
    main()
