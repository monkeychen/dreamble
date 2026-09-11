#!/usr/bin/env python3
"""mowen-download.py - 下载墨问关注用户的最新笔记到本地 Markdown.

数据链路:
  1. mocli disco activity --recent <range>   发现关注的人发的新笔记（元数据）
  2. POST note.mowen.cn/api/note/wxa/v1/note/show  逐篇拉取完整正文（匿名可访问公开笔记）

用法:
  # 拉最近 24h 关注的人新笔记
  python3 mowen-download.py --recent 24h

  # 指定笔记 ID（可多个）
  python3 mowen-download.py --note-id ID1 ID2

  # 指定输出目录（默认 tmp/mowen-downloads）
  python3 mowen-download.py --recent 24h --out /path/to/dir

依赖: mocli（已认证）+ 标准库。付费笔记匿名接口返回 ASSET_NOT_FOUND，
     脚本会落元数据占位文件并标注「付费」。
"""

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

SHOW_API = "https://note.mowen.cn/api/note/wxa/v1/note/show"
API_HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://note.mowen.cn",
    "Referer": "https://note.mowen.cn/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}


def run_mocli(args: list[str]) -> dict:
    """跑 mocli 命令并解析 JSON 输出。"""
    r = subprocess.run(["mocli", *args], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"mocli {' '.join(args)} 失败: {r.stderr[:300]}")
    return json.loads(r.stdout)


def discover_follow_notes(recent: str) -> dict[str, dict]:
    """从动态里提取关注的人发的新笔记，返回 {note_id: {author, title, paid}}。"""
    d = run_mocli(["disco", "activity", "--recent", recent])
    reply = d.get("reply", {})
    notes_meta = reply.get("notes", {})
    users = reply.get("users", {})
    result: dict[str, dict] = {}
    for detail_map, paid in (("follow_notes", False), ("follow_fee_notes", True)):
        for eid, ev in (reply.get(detail_map) or {}).items():
            nid = ev.get("note_id")
            if not nid:
                continue
            meta = notes_meta.get(nid, {})
            author_uid = ev.get("note_uid") or meta.get("uid", "")
            result[nid] = {
                "author": users.get(author_uid, {}).get("name", author_uid),
                "title": meta.get("title", nid),
                "paid": paid,
                # joins 是合集更新的子笔记
                "joins": ev.get("joins") or [],
            }
    return result


def fetch_note(note_id: str) -> dict | None:
    """调 note/show 拉取笔记完整数据；付费/不存在返回 None。"""
    req = urllib.request.Request(
        SHOW_API,
        data=json.dumps({"uuid": note_id}).encode(),
        headers=API_HEADERS,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            d = json.loads(resp.read())
    except Exception as e:
        print(f"  ! {note_id} 请求失败: {e}", file=sys.stderr)
        return None
    if "detail" not in d:
        return None  # 付费墙 ASSET_NOT_FOUND 等
    return d


class HtmlToMarkdown(HTMLParser):
    """墨问正文 HTML -> Markdown 的最小转换器（覆盖 p/h1-3/strong/em/a/ul/ol/li/quote/code/img/audio）。"""

    BLOCK_TAGS = {"p", "h1", "h2", "h3", "blockquote", "pre", "li", "div"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.list_stack: list[str] = []
        self.href_stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h1", "h2", "h3"):
            self.out.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "p":
            self.out.append("\n\n")
        elif tag == "strong" or tag == "b":
            self.out.append("**")
        elif tag == "em" or tag == "i":
            self.out.append("*")
        elif tag == "code" and "pre" not in getattr(self, "_in_pre", []):
            self.out.append("`")
        elif tag == "pre":
            self.out.append("\n\n```\n")
        elif tag == "a":
            self.href_stack.append(a.get("href", ""))
            self.out.append("[")
        elif tag in ("ul", "ol"):
            self.list_stack.append(tag)
        elif tag == "li":
            marker = "-" if not self.list_stack or self.list_stack[-1] == "ul" else "1."
            indent = "  " * max(0, len(self.list_stack) - 1)
            self.out.append(f"\n{indent}{marker} ")
        elif tag == "blockquote":
            self.out.append("\n\n> ")
        elif tag == "img":
            src = a.get("src", "")
            alt = a.get("alt", "图片")
            if src:
                self.out.append(f"\n\n![{alt}]({src})\n\n")
        elif tag == "br":
            self.out.append("\n")
        elif tag in ("audio", "video"):
            src = a.get("src", "")
            if src:
                self.out.append(f"\n\n[音频/视频]({src})\n\n")

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "p", "li", "blockquote"):
            self.out.append("\n")
        elif tag in ("strong", "b"):
            self.out.append("**")
        elif tag in ("em", "i"):
            self.out.append("*")
        elif tag == "code":
            self.out.append("`")
        elif tag == "pre":
            self.out.append("\n```\n")
        elif tag == "a":
            href = self.href_stack.pop() if self.href_stack else ""
            self.out.append(f"]({href})")
        elif tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        self.out.append(data)

    def text(self) -> str:
        raw = "".join(self.out)
        # 压缩 3+ 连续空行
        return re.sub(r"\n{3,}", "\n\n", raw).strip()


def html_to_md(html: str) -> str:
    p = HtmlToMarkdown()
    p.feed(html)
    return p.text()


def safe_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|\s]+', "-", name).strip("-")[:60]


def save_note(note_id: str, data: dict, out_dir: Path) -> Path:
    detail = data["detail"]
    nb = detail["noteBase"]
    user = data.get("user", {}).get("base", {})
    stat = detail.get("noteStat", {})
    flag = detail.get("noteFlag", {})

    created = datetime.fromtimestamp(int(nb.get("createdAt") or 0)).strftime("%Y-%m-%d")
    title = nb.get("title") or note_id
    author = user.get("name", "")
    path = out_dir / f"{created}-{safe_filename(title)}-{note_id[:6]}.md"

    meta = {
        "title": title,
        "author": author,
        "note_id": note_id,
        "url": f"https://note.mowen.cn/detail/{note_id}",
        "created_at": nb.get("createdAt"),
        "public_at": nb.get("publicAt"),
        "word_count": None,
        "stat": {k: stat.get(k) for k in ("duv", "favor", "collect", "comment", "share")},
    }
    body_md = html_to_md(nb.get("content", ""))
    tags = [t.get("name") for t in (detail.get("noteTags") or []) if t.get("name")]

    lines = [
        "---",
        *[f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in meta.items()],
        f"tags: {json.dumps(tags, ensure_ascii=False)}",
        "---",
        "",
        body_md,
        "",
        f"*原文: [{title}]({meta['url']})*",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    ap = argparse.ArgumentParser(description="下载墨问笔记到本地 Markdown")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--recent", help="时间范围，如 24h / today / yesterday（走 mocli disco）")
    g.add_argument("--note-id", nargs="+", help="直接指定笔记 ID")
    ap.add_argument("--out", default="tmp/mowen-downloads", help="输出目录（默认 tmp/mowen-downloads）")
    ap.add_argument("--force", action="store_true", help="已存在时覆盖")
    args = ap.parse_args()

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.recent:
        found = discover_follow_notes(args.recent)
        if not found:
            print(f"最近 {args.recent} 没有关注的人发新笔记")
            return
        print(f"发现 {len(found)} 篇新笔记:")
        for nid, m in found.items():
            pay = " [付费]" if m["paid"] else ""
            print(f"  - {m['author']}: {m['title']}{pay}")
    else:
        found = {nid: {"author": "", "title": nid, "paid": False} for nid in args.note_id}

    ok = paid = skip = fail = 0
    for nid, m in found.items():
        existing = list(out_dir.glob(f"*-{nid[:6]}.md"))
        if existing and not args.force:
            print(f"= {m['title']} 已存在，跳过")
            skip += 1
            continue
        data = fetch_note(nid)
        if data is None:
            if m["paid"]:
                # 付费笔记：落元数据占位
                p = out_dir / f"PAID-{safe_filename(m['title'])}-{nid[:6]}.md"
                p.write_text(
                    f"---\ntitle: {json.dumps(m['title'], ensure_ascii=False)}\n"
                    f"note_id: \"{nid}\"\npaid: true\n"
                    f"url: https://note.mowen.cn/detail/{nid}\n---\n\n"
                    f"付费笔记，匿名接口无法获取正文，请在墨问小程序打开。\n",
                    encoding="utf-8",
                )
                paid += 1
                print(f"$ {m['title']} → 付费占位: {p.name}")
            else:
                fail += 1
                print(f"! {m['title']} 拉取失败")
        else:
            p = save_note(nid, data, out_dir)
            ok += 1
            print(f"+ {m['title']} → {p.name}")
        time.sleep(0.5)  # 温和限速

    print(f"\n完成: 成功 {ok} / 付费占位 {paid} / 跳过 {skip} / 失败 {fail}，输出目录: {out_dir}")


if __name__ == "__main__":
    main()
