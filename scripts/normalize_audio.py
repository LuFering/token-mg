# -*- coding: utf-8 -*-
"""
音频归一化（两遍法，修正版）。

上一版的问题：压缩器的 makeup 增益与 volume 增益叠加，导致过冲到 -10 LUFS。
本版：先跑一遍"只压缩不增益"的链，量出实际响度，再精确补足到目标。
并用 loudnorm 的测量模式做最终校验。
"""
import os
import re
import subprocess

SRC = r"E:\AI自媒体\粗剪视频"
OUT = r"D:\cut\token-mg\assets\voice"
os.makedirs(OUT, exist_ok=True)

TARGET_I = -15.0
TP = -1.5
COMP = "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=180"


def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path,
                        "-af", "ebur128=peak=true", "-f", "null", os.devnull],
                       capture_output=True, text=True, errors="ignore")
    I = TPk = None
    for line in r.stderr.splitlines():
        s = line.strip()
        if s.startswith("I:") and I is None:
            m = re.search(r"I:\s*(-?[\d.]+)", s)
            if m:
                I = float(m.group(1))
        if "Peak:" in s and TPk is None:
            m = re.search(r"Peak:\s*(-?[\d.]+)", s)
            if m:
                TPk = float(m.group(1))
    return I, TPk


def run(src, dst, af):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn",
                    "-af", af, "-c:a", "aac", "-b:a", "256k", "-ar", "48000", dst],
                   check=True)


def main():
    print("目标 %.1f LUFS / 真峰值 %.1f dBTP" % (TARGET_I, TP))
    print()
    for i in range(1, 6):
        src = os.path.join(SRC, "%d.mp4" % i)
        dst = os.path.join(OUT, "%d.m4a" % i)
        tmp = os.path.join(OUT, "_t%d.m4a" % i)

        # 第 1 遍：高通 + 轻压缩（不带任何增益），量出响度
        stage1 = "highpass=f=70," + COMP
        run(src, tmp, stage1)
        I1, _ = measure(tmp)

        # 第 2 遍：按差值精确补足，再用限幅器兜住峰值
        gain = TARGET_I - I1
        lim = 10 ** (TP / 20.0)
        chain = "%s,volume=%.2fdB,alimiter=limit=%.4f:level=false" % (stage1, gain, lim)
        run(src, dst, chain)

        I2, TP2 = measure(dst)
        err = I2 - TARGET_I if I2 is not None else None
        print("  %d.mp4  压缩后 %6.2f LUFS  ->  增益 %+5.2f dB  ->  成品 %6.2f LUFS "
              "(偏差 %+.2f)  峰值 %.1f dBTP"
              % (i, I1, gain, I2, err, TP2))
        os.remove(tmp)

    print()
    print("完成 ->", OUT)


if __name__ == "__main__":
    main()
