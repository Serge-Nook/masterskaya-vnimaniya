"""Урезает Noto Sans SC до символов из перевода (mv/i18n/zh.ts).

curl -L -o /tmp/NotoSansSC.ttf "https://github.com/google/fonts/raw/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"
python tools/subset_cjk.py /tmp/NotoSansSC.ttf
"""
import string
import sys
from pathlib import Path

from fontTools import subset

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / "mv" / "i18n" / "zh.ts").read_text(encoding="utf-8")
chars = {c for c in text if ord(c) > 0x2E7F} | set(string.printable) | set("，。：；！？、（）《》“”……——·")
opts = subset.Options()
opts.layout_features = ["*"]
opts.name_IDs = ["*"]
opts.drop_tables += ["BASE"]
font = subset.load_font(sys.argv[1], opts)
s = subset.Subsetter(opts)
s.populate(text="".join(sorted(chars)))
s.subset(font)
out = ROOT / "mv" / "data" / "fonts" / "NotoSansSC-subset.ttf"
subset.save_font(font, str(out), opts)
print(out, out.stat().st_size, len(chars))
