#!/usr/bin/env python3
"""掃描 assets/ 裡的作品資料夾，產生 content/content.js（網站讀的內容清單）。

用法：直接雙擊專案根目錄的「更新網站內容.command」，或在終端機執行
    python3 tools/build-content.py

規則：
- 資料夾或檔名以 _ 開頭的會被忽略（例如 _example-project 是範例）。
- 圖片依檔名排序（01.jpg, 02.jpg …）；名字叫 cover.* 的當封面，沒有就用第一張。
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
IMG = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def parse_md(path: Path):
    """回傳 (front-matter dict, body 文字)。front matter 是檔案開頭 --- 之間的 key: value。"""
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    meta, body = {}, text
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = m.group(2)
    return meta, body.strip()


def blocks(body: str, folder: Path):
    """把內文拆成段落／小標／圖片區塊。"""
    out = []
    for chunk in re.split(r"\n\s*\n", body):
        chunk = chunk.strip()
        if not chunk:
            continue
        im = re.match(r"^!\[(.*?)\]\((.*?)\)$", chunk)
        if im:
            src = im.group(2)
            out.append({"type": "img", "alt": im.group(1), "src": src if src.startswith("http") else rel(folder / src)})
        elif chunk.startswith("#"):
            out.append({"type": "h", "text": chunk.lstrip("# ").strip()})
        else:
            out.append({"type": "p", "text": chunk})
    return out


def images_in(folder: Path):
    return sorted([p for p in folder.iterdir() if p.suffix.lower() in IMG and not p.name.startswith((".", "_"))], key=lambda p: p.name.lower())


def warn_skipped():
    """提醒：底線開頭的資料夾（範例）裡如果有內容，會被略過。"""
    for sub in ("04-design", "05-writing", "06-newsletter"):
        for d in (ASSETS / sub).glob("_*"):
            if d.is_dir() and any(d.iterdir()):
                print(f"（提醒）略過範例資料夾 {sub}/{d.name}：名稱以底線開頭的不會出現在網站上。要新增內容，請新建不以底線開頭的資料夾。")


def build():
    warn_skipped()
    site = {"about": {}, "contact": [], "design": [], "writing": [], "newsletter": {}, "issues": []}

    # ---- 關於我 / 聯絡 ----
    folder = ASSETS / "03-about-contact"
    meta, body = parse_md(folder / "about.md")
    portrait = next((p for p in (folder.glob("portrait.*")) if p.suffix.lower() in IMG), None)
    site["about"] = {"name": meta.get("name", ""), "tagline": meta.get("tagline", ""),
                     "blocks": blocks(body, folder), "portrait": rel(portrait) if portrait else ""}
    _, contact = parse_md(folder / "contact.md")
    for line in contact.split("\n"):
        line = line.strip()
        if ":" not in line or line.startswith("#"):
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if not (k and v):
            continue
        # 格式：名稱: 顯示文字 | 連結（連結可省略）
        text, _, url = [x.strip() for x in v.partition("|")]
        if not url:
            if re.match(r"^(https?://|mailto:|tel:)", text):
                url = text
            elif re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", text):
                url = "mailto:" + text
        if text.startswith("mailto:"):
            text = text[len("mailto:"):]
        site["contact"].append({"label": k, "text": text, "url": url})
    cv = next(iter(folder.glob("cv.pdf")), None)
    if cv:
        site["contact"].append({"label": "CV", "text": "CV (PDF)", "url": rel(cv)})

    # ---- 平面設計 ----
    folder = ASSETS / "04-design"
    for d in sorted([p for p in folder.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))], reverse=True):
        meta, body = parse_md(d / "info.md")
        imgs = images_in(d)
        cover = next((p for p in imgs if p.stem.lower() == "cover"), imgs[0] if imgs else None)
        date = meta.get("date", "")
        year = meta.get("year", "") or (date[:4] if date else "")   # 有 date 就從 date 取年份；沒有 date 才看舊的 year 欄位
        site["design"].append({
            "slug": d.name, "title": meta.get("title", d.name), "year": year, "date": date, "role": meta.get("role", ""),
            "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            "description": blocks(body, d), "cover": rel(cover) if cover else "",
            "images": [rel(p) for p in imgs if p != cover],
        })
    site["design"].sort(key=lambda x: (x["date"] or x["year"]), reverse=True)

    # ---- 隨筆 ----
    folder = ASSETS / "05-writing"
    for d in sorted([p for p in folder.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))], reverse=True):
        meta, body = parse_md(d / "index.md")
        site["writing"].append({
            "slug": d.name, "title": meta.get("title", d.name), "date": meta.get("date", ""),
            "source": meta.get("source", ""), "url": meta.get("url", ""),
            "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            "blocks": blocks(body, d),
        })
    site["writing"].sort(key=lambda x: x["date"], reverse=True)

    # ---- 電子報 ----
    folder = ASSETS / "06-newsletter"
    if folder.exists():
        meta, body = parse_md(folder / "newsletter.md")
        site["newsletter"] = {"subscribe": meta.get("subscribe", ""), "subscribeLabel": meta.get("subscribeLabel", ""), "form": meta.get("form", ""), "blocks": blocks(body, folder)}
        for d in sorted([p for p in folder.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))], reverse=True):
            meta, body = parse_md(d / "index.md")
            site["issues"].append({"slug": d.name, "title": meta.get("title", d.name), "date": meta.get("date", ""),
                                   "url": meta.get("url", ""), "blocks": blocks(body, d)})
        site["issues"].sort(key=lambda x: x["date"], reverse=True)

    out = ROOT / "content" / "content.js"
    out.parent.mkdir(exist_ok=True)
    out.write_text("// 由 tools/build-content.py 自動產生，請不要手動修改\nwindow.SITE = " + json.dumps(site, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
    print(f"完成：設計作品 {len(site['design'])} 件、隨筆 {len(site['writing'])} 篇、電子報 {len(site['issues'])} 期、聯絡方式 {len(site['contact'])} 項 → content/content.js")


if __name__ == "__main__":
    try:
        build()
    except Exception as e:
        print("發生錯誤：", e)
        sys.exit(1)
