# -*- coding: utf-8 -*-
"""
逐条检测人脸位置，输出每条的最优裁切窗口。

动机：2.mp4 是窄幅画面（去掉黑边后 1212x1080），裁进 4:3 窗口需上下切 171px。
      切在哪由"人脸在哪"决定，而不是机械居中。
同时校验另外三条（满幅 4:3）的人脸是否在安全区内。
"""
import json
import os
import subprocess

import cv2
import numpy as np

SRC = r"E:\AI自媒体\粗剪视频"
TMP = os.path.join(os.environ["TEMP"], "facecheck")
os.makedirs(TMP, exist_ok=True)

# 每条：源片 + 已裁黑边的窗口 (w,h,x,y)
BASE = {
    1: (1440, 1080, 0, 0),
    2: (1212, 1080, 182, 0),
    3: (1440, 1080, 0, 0),
    4: (1440, 1080, 0, 0),
    5: (1920, 1074, 0, 6),
}
# 目标窗口比例
WIN = {1: 620 / 465, 2: 620 / 465, 3: 620 / 465, 4: 620 / 465, 5: 864 / 486}

cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def sample_faces(n, base, k=5):
    """在整段视频里采样 k 帧，检出所有人脸框"""
    w, h, x0, y0 = base
    p = os.path.join(SRC, "%d.mp4" % n)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip())
    boxes = []
    for i in range(k):
        t = dur * (i + 0.5) / k
        f = os.path.join(TMP, "f%d_%d.png" % (n, i))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % t, "-i", p,
                        "-frames:v", "1", "-vf", "crop=%d:%d:%d:%d" % (w, h, x0, y0), f], check=True)
        img = cv2.imread(f)
        if img is None:
            continue
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(g, scaleFactor=1.08, minNeighbors=6,
                                         minSize=(int(h * 0.12), int(h * 0.12)))
        for (fx, fy, fw, fh) in faces:
            boxes.append((fx, fy, fw, fh))
    return boxes, (w, h)


def main():
    report = {}
    for n in range(1, 6):
        boxes, (w, h) = sample_faces(n, BASE[n])
        if boxes:
            xs = [b[0] for b in boxes]
            ys = [b[1] for b in boxes]
            ws = [b[2] for b in boxes]
            hs = [b[3] for b in boxes]
            # 人脸中心（取各帧均值）
            fcx = float(np.mean([x + ww / 2.0 for x, ww in zip(xs, ws)]))
            fcy = float(np.mean([y + hh / 2.0 for y, hh in zip(ys, hs)]))
            fh_avg = float(np.mean(hs))
        else:
            fcx, fcy, fh_avg = w / 2.0, h * 0.42, h * 0.18

        ratio = WIN[n]
        # 目标裁切窗口（在"已去黑边"的坐标系里）
        cw = w
        ch = int(round(cw / ratio))
        if ch <= h:
            # 需要上下裁
            # 让脸落在窗口上方 1/3 处（人像构图的常规）
            top = int(round(fcy - ch * 0.38))
            top = max(0, min(h - ch, top))
            cx0, cy0 = 0, top
        else:
            cw = int(round(h * ratio))
            ch = h
            left = int(round(fcx - cw / 2.0))
            left = max(0, min(w - cw, left))
            cx0, cy0 = left, 0

        report[n] = dict(
            base_w=w, base_h=h, out_w=cw, out_h=ch, crop_x=cx0, crop_y=cy0,
            face_center=[round(fcx, 1), round(fcy, 1)], face_h=round(fh_avg, 1),
            face_in_out=[round(fcx, 1), round(fcy - cy0, 1)],
        )
        print("  %d.mp4  去黑边 %dx%d  人脸中心(%.0f,%.0f) 高%.0f  "
              "-> 裁 %dx%d @ (%d,%d)  脸在窗内(%.0f,%.0f)"
              % (n, w, h, fcx, fcy, fh_avg, cw, ch, cx0, cy0, fcx - cx0, fcy - cy0))

    with open(r"D:\cut\token-mg\scripts\face_meta.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\nface_meta.json 已写出")


if __name__ == "__main__":
    main()
