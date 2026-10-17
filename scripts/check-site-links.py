#!/usr/bin/env python3
"""Validate local HTML links and images before publishing GitHub Pages."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import sys

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', '.github', 'node_modules'}
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []
        self.images = []
        self.ids = set()
        self.duplicate_ids = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            if a['id'] in self.ids:
                self.duplicate_ids.append(a['id'])
            self.ids.add(a['id'])
        if tag == 'a' and a.get('href'):
            self.targets.append((tag, a['href']))
        if tag in ('img', 'script', 'link'):
            k = 'src' if tag != 'link' else 'href'
            if a.get(k):
                self.targets.append((tag, a[k]))
                if tag == 'img':
                    self.images.append(a)
errors = []
count = 0
for html in sorted(ROOT.rglob('*.html')):
    if any(x in SKIP for x in html.relative_to(ROOT).parts):
        continue
    doc = Links()
    try:
        doc.feed(html.read_text(encoding='utf-8'))
    except Exception as e:
        errors.append(f'{html.relative_to(ROOT)}: HTML parsing failed: {e}')
        continue
    for duplicate in doc.duplicate_ids:
        errors.append(f'{html.relative_to(ROOT)}: duplicate HTML id #{duplicate}')
    for tag, value in doc.targets:
        url = urlsplit(value)
        if url.scheme or url.netloc or value.startswith(('mailto:', 'tel:', 'javascript:', 'data:')):
            continue
        if not url.path and not url.fragment:
            continue
        decoded = unquote(url.path)
        if not decoded and url.fragment:
            if unquote(url.fragment) not in doc.ids:
                errors.append(f'{html.relative_to(ROOT)}: missing in-page anchor #{url.fragment}')
            continue
        if decoded.startswith('/'):
            target = ROOT / decoded.lstrip('/')
        else:
            target = html.parent / decoded
        target = target.resolve()
        if not target.is_relative_to(ROOT.resolve()):
            errors.append(f'{html.relative_to(ROOT)}: path escapes site root: {value}')
            continue
        if target.is_dir():
            target = target / 'index.html'
        count += 1
        if not target.is_file():
            errors.append(f'{html.relative_to(ROOT)}: missing {tag} target {value}')
    for attrs in doc.images:
        if not attrs.get('alt') and 'alt' not in attrs:
            errors.append(f'{html.relative_to(ROOT)}: image missing alt attribute')
print(f'Checked {count} local references.')
if errors:
    print('\n'.join(errors))
    sys.exit(1)
print('All checked local references resolve.')
