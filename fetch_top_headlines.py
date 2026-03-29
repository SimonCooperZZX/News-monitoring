#!/usr/bin/env python3
"""
Fetch top headlines from NewsAPI.org and write a Markdown report.

Requires environment variable: NEWS_API_KEY

Optional:
  NEWS_COUNTRY — ISO 3166-1 alpha-2 (e.g. us, gb). If set, uses category=general
                 for that country. If unset, uses keyword search q (see NEWS_QUERY)
                 for broader international-style results (NewsAPI has no single
                 “worldwide” top-headlines mode).
  NEWS_QUERY — Used only when NEWS_COUNTRY is unset. Default: world
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import Any

import requests

NEWSAPI_TOP = "https://newsapi.org/v2/top-headlines"
OUTPUT_FILE = "news_report.md"
PAGE_SIZE = 10


def _escape_md_cell(text: str) -> str:
    """Escape pipes and newlines so Markdown tables stay valid."""
    s = text.replace("\r\n", " ").replace("\n", " ").replace("|", "\\|")
    return s.strip()


def _build_params() -> dict[str, Any]:
    country = os.getenv("NEWS_COUNTRY", "").strip()
    if country:
        return {
            "country": country,
            "category": "general",
            "pageSize": PAGE_SIZE,
        }
    q = os.getenv("NEWS_QUERY", "world").strip() or "world"
    return {
        "q": q,
        "pageSize": PAGE_SIZE,
    }


def main() -> int:
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        print("错误: 请设置环境变量 NEWS_API_KEY", file=sys.stderr)
        return 1

    headers = {
        "X-Api-Key": api_key,
        "User-Agent": "fetch_top_headlines/1.0 (Python; NewsAPI)",
    }
    params = _build_params()

    try:
        r = requests.get(NEWSAPI_TOP, headers=headers, params=params, timeout=30)
    except requests.RequestException as e:
        print(f"请求失败: {e}", file=sys.stderr)
        return 1

    try:
        data = r.json()
    except ValueError:
        print("响应不是合法 JSON", file=sys.stderr)
        return 1

    if r.status_code != 200 or data.get("status") != "ok":
        msg = data.get("message", r.text[:500])
        code = data.get("code", "")
        print(f"API 错误 ({r.status_code}) {code}: {msg}", file=sys.stderr)
        return 1

    articles: list[dict[str, Any]] = data.get("articles") or []
    articles = articles[:PAGE_SIZE]

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# 热门头条 (Top Headlines)",
        "",
        f"_抓取时间: {now}_",
        "",
        "| # | 标题 | 来源 | 发布时间 | 原文链接 |",
        "|---|------|------|----------|----------|",
    ]

    for i, a in enumerate(articles, start=1):
        title = _escape_md_cell(a.get("title") or "")
        src = a.get("source") or {}
        name = _escape_md_cell(str(src.get("name") or ""))
        published = _escape_md_cell(a.get("publishedAt") or "")
        url = (a.get("url") or "").strip()
        url_cell = f"[链接]({url})" if url else ""

        lines.append(f"| {i} | {title} | {name} | {published} | {url_cell} |")

    lines.append("")

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILE)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"已写入 {out_path}，共 {len(articles)} 条。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
