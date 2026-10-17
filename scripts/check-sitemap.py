#!/usr/bin/env python3
"""Validate sitemap URL structure and local targets for GitHub Pages."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET
import sys

root = Path(__file__).resolve().parents[1]
sitemap = root / "sitemap.xml"
site = "bershagames.github.io"
errors = []
seen = set()
try:
    tree = ET.parse(sitemap)
    entries = tree.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
except (ET.ParseError, OSError) as exc:
    print(f"Sitemap XML invalid: {exc}")
    sys.exit(1)
for node in entries:
    url = (node.text or "").strip()
    if url in seen:
        errors.append(f"Duplicate sitemap URL: {url}")
    seen.add(url)
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc != site or parts.query or parts.fragment:
        errors.append(f"Invalid sitemap URL: {url}")
        continue
    target = (root / unquote(parts.path).lstrip("/")).resolve()
    if not target.is_relative_to(root.resolve()):
        errors.append(f"Path outside repository: {url}")
        continue
    if target.is_dir():
        target /= "index.html"
    if not target.is_file():
        errors.append(f"Missing sitemap page: {url}")
if not entries:
    errors.append("Sitemap has no URLs")
print(f"Checked {len(entries)} sitemap URLs.")
if errors:
    print("\n".join(errors))
    sys.exit(1)
print("Sitemap URLs and local pages verified.")
