#!/usr/bin/env python3
"""Check gallery manifest paths, naming, and image headers."""
import json
import struct
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = root / 'assets/gallery-manifest.json'
expected = {'block-merge-rush', 'esnaf', 'transit-empire-world'}
errors = []
try:
    data = json.loads(manifest.read_text(encoding='utf-8'))
except (OSError, ValueError) as exc:
    print(f'Invalid gallery manifest: {exc}')
    sys.exit(1)
if data.get('schemaVersion') != 1 or set(data.get('galleries', {})) != expected:
    errors.append('Invalid gallery schema or game keys')
total = 0
for game, files in data.get('galleries', {}).items():
    if game not in expected or not isinstance(files, list):
        errors.append(f'Invalid gallery: {game}')
        continue
    if len(files) != len(set(files)):
        errors.append(f'Duplicate filenames: {game}')
    for name in files:
        if not isinstance(name, str) or len(name) != 7 or not name[:2].isdigit() or name[2:] != '.webp':
            errors.append(f'Invalid filename: {game}/{name}')
            continue
        path = root / 'assets/screenshots' / game / name
        if not path.is_file():
            errors.append(f'Missing listed image: {path.relative_to(root)}')
            continue
        if path.read_bytes()[:4] != b'RIFF' or path.read_bytes()[8:12] != b'WEBP':
            errors.append(f'Invalid WebP header: {path.relative_to(root)}')
        total += 1
print(f'Validated {total} published gallery image references.')
if errors:
    print('\n'.join(errors))
    sys.exit(1)
print('Gallery manifest valid.')
