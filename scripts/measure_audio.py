# -*- coding: utf-8 -*-
"""实测 5 条源片的音频响度（用户反馈"声音小"，先量化）。"""
import os
import re
import subprocess
import sys

SRC = r"E:\AI自媒体\粗剪视频"

print("=== 源片音频实测 ===")
rows = []
for i in range(1, 6):
    p = os.path.join(SRC, "%d.mp4" % i)
    a = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "volumedetect",
                        "-f", "null", os.devnull],
                       capture_output=True, text=True, errors="ignore").stderr
    mean = maxv = None
    for line in a.splitlines():
        if "mean_volume" in line:
            m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", line)
            if m:
                mean = float(m.group(1))
        if "max_volume" in line:
            m = re.search(r"max_volume:\s*(-?[\d.]+) dB", line)
            if m:
                maxv = float(m.group(1))
    b = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "ebur128",
                        "-f", "null", os.devnull],
                       capture_output=True, text=True, errors="ignore").stderr
    lufs = None
    for line in b.splitlines():
        if line.strip().startswith("I:"):
            m = re.search(r"I:\s*(-?[\d.]+)\s*LUFS", line)
            if m:
                lufs = float(m.group(1))
    rows.append((i, mean, maxv, lufs))
    print("  %d.mp4  peak=%s dB  mean=%s dB  I=%s LUFS"
          % (i, maxv, mean, lufs))

print()
print("=== 参考：社交/网络视频的常见目标 ===")
print("  平台成片响度通常 -14 ~ -16 LUFS；低于 -20 LUFS 会被听感判定为'声音小'")
for i, mean, maxv, lufs in rows:
    if lufs is not None:
        need = -15.0 - lufs
        print("  %d.mp4 需提升约 %.1f dB 才到 -15 LUFS" % (i, need))
