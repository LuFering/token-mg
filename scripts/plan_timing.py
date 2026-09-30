# -*- coding: utf-8 -*-
"""
重写 index.html 的编排段（节奏改为"每条落定后播完，再飞入下一条"）。

节奏模型：
  每条视频：升入 -> 落定 -> 立即起播 -> 播完 -> 下一条升入
  最后一条：落定 -> 播放 -> 停稳 -> 放大铺满 -> 继续播到结束

素材已经用 tpad 补足到足够长，所以 data-duration 直接取所需长度即可，
视频播完后画面自动停在末帧（等于"播放完"后保持），不会黑屏。
"""
import io
import re

P = r"D:\cut\token-mg\index.html"
s = io.open(P, encoding="utf-8").read()

# ── 节奏参数 ────────────────────────────────────────────
# 单条视频的真实时长（源片，秒）
REAL = {1: 0.533, 2: 0.567, 3: 1.000, 4: 0.833, 5: 4.233}
# 每条升入的时刻（累积）：前一条落定 + 播放时长 + 一点呼吸
LEAD = 0.55          # 开场留白
RISE = 0.62          # 升入
OVER = 0.26          # settle
PRESS = 0.09         # press
LAND = RISE + OVER + PRESS      # 0.97

BREATH = 0.42        # 视频播完后再留一点呼吸，观众视线才转移
HOLD = 1.05          # 压轴停稳后停留再放大
ZOOM = 1.05

sfx_map = []


def main():
    t = LEAD
    cues = {}
    for i in range(1, 6):
        cues[i] = t
        land = t + LAND
        dur = REAL[i] + BREATH
        t = land + dur
        print("  第%d条  升入 %.2fs  落定 %.2fs  播放 %.3fs  结束 %.2fs"
              % (i, cues[i], land, REAL[i], land + dur))

    total = t
    hero_land = cues[5] + LAND
    zoom_at = hero_land + HOLD
    zoom_end = zoom_at + ZOOM
    total = zoom_end + (REAL[5] - (zoom_end - hero_land)) if REAL[5] > (zoom_end - hero_land) else zoom_end
    # 压轴视频要播完：至少 hero_land + REAL[5]
    total = max(total, hero_land + REAL[5] + 0.35)
    print("\n  压轴放大 %.2f -> %.2f   全片 %.3fs" % (zoom_at, zoom_end, total))

    # 落点（保持原有构图）
    LAY = [
        ("s1", [ 634, 318], 0.87, -8.5, 1),
        ("s2", [1272, 352], 0.85,  6.8, 2),
        ("s3", [ 682, 728], 0.89,  5.2, 3),
        ("s4", [1238, 744], 0.86, -6.4, 4),
        ("s5", [ 960, 540], 0.90,  0.0, 5),
    ]

    lay_js = []
    for sid, at, sc, rot, n in LAY:
        lay_js.append('          { id: "%s", at: [%d, %d], s: %s, rot: %s, cue: %s }'
                      % (sid, at[0], at[1], sc, rot, round(cues[n], 3)))
    lay_block = "        var LAY = [\n" + ",\n".join(lay_js) + "\n        ];\n"

    # SFX 钉帧：升入那一下
    for sid, at, sc, rot, n in LAY[:5]:
        sfx_map.append(("x-s%d" % n, round(cues[n] + 0.02, 3)))
    sfx_map.append(("x-zoom", round(zoom_at, 3)))

    print("\n  SFX 钉帧：")
    for k, v in sfx_map:
        print("    %-8s %.3f" % (k, v))

    return cues, total, zoom_at, zoom_end, lay_block


if __name__ == "__main__":
    main()
