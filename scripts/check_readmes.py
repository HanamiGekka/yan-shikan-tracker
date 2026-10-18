"""Check the four README entry points without reading runtime data."""
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('README.md', 'README.zh-CN.md', 'README.ja.md', 'README.zh-TW.md')
errors = []
checked = 0

def anchors(text):
    result = set(re.findall(r'<a\s+id=["\x27]([^"\x27]+)', text))
    seen = {}
    for title in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', text, re.M):
        slug = re.sub(r'[^\w\- ]', '', title.lower()).replace(' ', '-')
        number = seen.get(slug, 0)
        seen[slug] = number + 1
        result.add(slug + (f'-{number}' if number else ''))
    return result

for name in NAMES:
    path = ROOT / name
    if not path.is_file():
        errors.append(f'Missing README: {name}')
        continue
    text = path.read_text(encoding='utf-8-sig')
    first = text.splitlines()[0]
    for target in NAMES:
        if f']({target})' not in first:
            errors.append(f'Missing language navigation: {name} -> {target}')
    if len(re.findall(r'^# ', text, re.M)) != 1:
        errors.append(f'Expected one top-level heading: {name}')
    if len(re.findall(r'^```', text, re.M)) % 2:
        errors.append(f'Unclosed code fence: {name}')
    prose = re.sub(r'```.*?```', '', text, flags=re.S)
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', prose):
        url = urlsplit(target.strip().strip('<>'))
        if url.scheme or target.startswith('//'):
            continue
        dest = path if not url.path else (path.parent / unquote(url.path)).resolve()
        checked += 1
        if not dest.is_relative_to(ROOT) or not dest.is_file():
            errors.append(f'Broken or out-of-tree link: {name} -> {target}')
        elif url.fragment and dest.suffix == '.md':
            if unquote(url.fragment) not in anchors(dest.read_text(encoding='utf-8-sig')):
                errors.append(f'Broken anchor: {name} -> {target}')

print(json.dumps({'readmes': len(NAMES), 'local_links_checked': checked, 'errors': errors}, indent=2))
raise SystemExit(1 if errors else 0)
