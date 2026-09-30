# -*- coding: utf-8 -*-
"""
生成五条画面素材（供合成使用）。

需求变化：
- 每条视频在"自己落定后立刻开始播放"，播完才轮到下一条升入。
  所以素材时长 = 该条到片尾所需的时间，不足部分用末帧定格补齐。
- 2.mp4 左右各有 182px 黑边（cropdetect 实测），先裁掉再垫定格。
- 裁切后统一为 4:3（前置卡）/ 16:9（压轴卡）的窗口比例，避免再引入黑边。
"""
import json
import os
import subprocess

SRC = r"E:\AI自媒体\粗剪视频"
OUT = r"D:\cut\token-mg\assets\media"
os.makedirs(OUT, exist_ok=True)

# 每条处理后的目标宽高比（前置 4:3，压轴 16:9）
CROP = {
    1: "1440:1080:0:0",      # 满幅 4:3
    2: "1212:1080:182:0",    # 去掉左右各 182 黑边
    3: "1440:1080:0:0",
    4: "1440:1080:0:0",
    5: "1920:1074:0:6",      # 去掉上下极细黑边
}
# 需要输出的总时长（秒）：由时间轴决定，稍后由 build 脚本回填，
# 这里先给一个足够长的上限，实际使用由 data-duration 截断。
TOTAL = 14.0


def probe_dur(p):
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    return float(o.stdout.strip())


def main():
    meta = {}
    for i in range(1, 6):
        src = os.path.join(SRC, "%d.mp4" % i)
        dst = os.path.join(OUT, "%d-pad.mp4" % i)
        crop = CROP[i]
        cw, ch, cx, cy = [int(x) for x in crop.split(":")]

        pad = max(0.05, TOTAL - probe_dur(src))
        vf = "crop=%d:%d:%d:%d,tpad=stop_mode=clone:stop_duration=%.3f" % (cw, ch, cx, cy, pad)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf,
                        "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                        "-pix_fmt", "yuv420p", "-r", "30", "-an", dst], check=True)

        od = probe_dur(dst)
        w = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height", "-of", "csv=p=0", dst],
                           capture_output=True, text=True).stdout.strip()
        meta[i] = dict(dur=round(od, 3), size=w, crop=crop)
        print("  %d-pad.mp4  裁 %s  -> %s  %.3fs" % (i, crop, w, od))

    with open(r"D:\cut\token-mg\scripts\media_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print("\nmedia_meta.json 已写出")


if __name__ == "__main__":
    main()
