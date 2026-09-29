# -*- coding: utf-8 -*-
"""把 index.html 里所有 data-automation 规范成合法的双引号属性 JSON。"""
import html
import json
import re
import sys

P = r"D:\cut\token-mg\index.html"
s = open(P, encoding="utf-8").read()

BACKSLASH = chr(92)
SQ = chr(39)
DQ = chr(34)


def normalize(raw):
    # 去掉可能混进来的转义反斜杠与包裹引号
    raw = raw.replace(BACKSLASH + SQ, SQ)
    raw = raw.replace(BACKSLASH + DQ, DQ)
    raw = raw.replace(BACKSLASH, "")
    raw = raw.strip().strip(SQ).strip(DQ)
    obj = json.loads(raw)
    txt = json.dumps(obj, separators=(",", ":"))
    return 'data-automation="%s"' % html.escape(txt, quote=True)


# 匹配 data-automation='...'  或  data-automation=\'...\'
pat = re.compile(r"data-automation=" + re.escape(BACKSLASH) + "?" + SQ + r"(.*?)" + re.escape(BACKSLASH) + "?" + SQ, re.S)

count = [0]


def rep(m):
    count[0] += 1
    try:
        return normalize(m.group(1))
    except Exception as e:
        print("  !! 解析失败 %r: %s" % (m.group(1)[:70], e))
        return m.group(0)


s2 = pat.sub(rep, s)
print("替换 %d 处" % count[0])
open(P, "w", encoding="utf-8").write(s2)

# 校验
ok = bad = 0
for m in re.finditer(r'id="([^"]+)"[^>]*data-automation="([^"]*)"', s2, re.S):
    raw = html.unescape(m.group(2))
    try:
        json.loads(raw)
        ok += 1
    except Exception as e:
        bad += 1
        print("  x %s: %s" % (m.group(1), e))
print("合法 %d 条，非法 %d 条" % (ok, bad))
sys.exit(1 if bad else 0)
