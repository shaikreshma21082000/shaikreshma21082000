#!/usr/bin/env python3
"""Refresh the latest-articles list in README.md from a Medium RSS feed.

Standard library only. If the feed cannot be fetched or parsed, the README is
left untouched and the script exits 0, so a Medium hiccup never fails the run.
"""
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, urlunsplit

FEED_URL = "https://medium.com/feed/@shaikreshma21082000"
README = "README.md"
START, END = "<!-- medium:start -->", "<!-- medium:end -->"
LIMIT = 5


def fetch_items():
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0 (profile-readme-updater)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        root = ET.fromstring(resp.read())
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not title or not link:
            continue
        parts = urlsplit(link)
        link = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))  # drop tracking query
        date = ""
        try:
            date = parsedate_to_datetime(item.findtext("pubDate") or "").strftime("%b %Y")
        except (TypeError, ValueError):
            pass
        items.append((title, link, date))
    return items[:LIMIT]


def render(items):
    lines = []
    for title, link, date in items:
        title = title.replace("[", "(").replace("]", ")")
        lines.append(f"- [{title}]({link})" + (f" · {date}" if date else ""))
    return "\n".join(lines)


def main():
    try:
        items = fetch_items()
    except Exception as exc:  # network error, Medium blocking the runner, bad XML...
        print(f"Medium feed unavailable ({exc}); leaving README unchanged.")
        return 0
    if not items:
        print("Feed returned no articles; leaving README unchanged.")
        return 0

    with open(README, encoding="utf-8") as fh:
        text = fh.read()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(text):
        print("Medium markers not found in README; nothing to do.")
        return 0

    block = f"{START}\n{render(items)}\n{END}"
    new_text = pattern.sub(lambda _m: block, text)
    if new_text == text:
        print("Articles already up to date.")
        return 0
    with open(README, "w", encoding="utf-8") as fh:
        fh.write(new_text)
    print(f"Updated README with {len(items)} articles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
