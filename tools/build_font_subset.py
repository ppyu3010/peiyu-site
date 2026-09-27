#!/usr/bin/env python3
"""把源流明體「瘦身」成網站實際用得到的字，轉成網頁用的 woff2。

用法：
    python3 tools/build_font_subset.py

會做的事：
1. 掃描 index.html、content/content.js，以及 assets/03~06 底下所有 .md 檔，
   收集網站上「實際會出現」的每一個字。
2. 用這份字清單，把你 Downloads 裡的完整字型（各 9MB）縮小成只含這些字，
   輸出成 assets/fonts/GenRyuMinTW-EL.woff2、GenRyuMinTW-B.woff2。
3. 複製字型的授權檔一起放進 assets/fonts/。

之後你新增很多文章、用到很多新的字，網頁上那些新字會暫時顯示成替代字型（不會壞掉，
只是字體不一樣），這時候重新執行這個程式一次就會補上新字。
"""
import shutil, subprocess, sys, tempfile
from pathlib import Path
from fontTools.ttLib import TTCollection

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = Path.home() / "Library" / "Fonts"   # 系統裡「純文字版」源流明體（沒有注音標示）；Downloads 裡那份是注音版，不要用
OUT_DIR = ROOT / "assets" / "fonts"

# 基本字元：拉丁字母、數字、常用標點符號、全形標點 —— 保證一定包含，即使目前文字裡沒出現
BASE_CHARS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    " .,:;!?()[]{}\"'`~@#$%^&*_+=-/\\|<>\n\t"
    "，。、；：？！「」『』（）【】《》〈〉…—～·、‧※△▲○●□■◇◆★☆"
)

SCAN_FILES = [ROOT / "index.html", ROOT / "content" / "content.js"]
SCAN_GLOBS = [
    ROOT / "assets" / "03-about-contact",
    ROOT / "assets" / "04-design",
    ROOT / "assets" / "05-writing",
    ROOT / "assets" / "06-newsletter",
]


def collect_chars() -> set:
    chars = set(BASE_CHARS)
    for f in SCAN_FILES:
        if f.exists():
            chars.update(f.read_text(encoding="utf-8", errors="ignore"))
    for folder in SCAN_GLOBS:
        for f in folder.rglob("*.md"):
            chars.update(f.read_text(encoding="utf-8", errors="ignore"))
    # 拿掉控制字元
    return {c for c in chars if c.isprintable() or c in "\n\t"}


def extract_tw_face(ttc_path: Path, tmp_dir: Path) -> Path:
    """.ttc 字型檔裡同時包著 TW／JP 兩個版本，取出「TW」（台灣、無注音標示）那一份存成單獨檔案。"""
    tc = TTCollection(str(ttc_path))
    for font in tc.fonts:
        if "TW" in (font["name"].getDebugName(6) or ""):
            out = tmp_dir / (ttc_path.stem + ".ttf")
            font.save(str(out))
            return out
    raise RuntimeError(f"{ttc_path} 裡找不到 TW 版本")


def subset_one(src: Path, out: Path, chars: set):
    text = "".join(sorted(chars))
    cmd = [
        sys.executable, "-m", "fontTools.subset", str(src),
        f"--text={text}",
        "--flavor=woff2",
        f"--output-file={out}",
        "--layout-features=*",
        "--glyph-names",
        "--symbol-cmap",
        "--legacy-cmap",
        "--notdef-glyph",
        "--notdef-outline",
        "--recommended-glyphs",
        "--name-IDs=*",
        "--name-legacy",
        "--name-languages=*",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"✕ {src.name} 失敗：\n{r.stderr}")
        return False
    print(f"✓ {out.name}  {out.stat().st_size / 1024:.0f} KB")
    return True


def main():
    el_ttc = FONT_DIR / "GenRyuMin-EL.ttc"
    b_ttc = FONT_DIR / "GenRyuMin-B.ttc"
    for f in (el_ttc, b_ttc):
        if not f.exists():
            print(f"找不到字型檔：{f}")
            sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chars = collect_chars()
    print(f"收集到 {len(chars)} 個不同的字／符號")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        el_src = extract_tw_face(el_ttc, tmp_dir)
        b_src = extract_tw_face(b_ttc, tmp_dir)
        ok1 = subset_one(el_src, OUT_DIR / "GenRyuMinTW-EL.woff2", chars)
        ok2 = subset_one(b_src, OUT_DIR / "GenRyuMinTW-B.woff2", chars)

    src_dir = Path.home() / "Downloads" / "BpmfGenRyuMin"
    for name in ("LICENSE-Gen.txt", "LICENSE-2.0.txt", "NOTICE.txt"):
        src = src_dir / name
        if src.exists():
            shutil.copy(src, OUT_DIR / name)

    if ok1 and ok2:
        print("完成。之後新增很多新文字時，重新執行這個程式一次即可補上。")


if __name__ == "__main__":
    main()
