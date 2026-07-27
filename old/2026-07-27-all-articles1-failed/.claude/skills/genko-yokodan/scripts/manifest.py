#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""原稿 1.md..10.md を話単位で棚卸しし、全走査用のバッチに割る。

使い方:
  python manifest.py                      # 話一覧(TSV)
  python manifest.py --batch 1800         # 走査バッチ一覧(TSV)
  python manifest.py --batch 1800 --json  # 同上をJSONで
  python manifest.py --summary            # 規模サマリのみ

TSV(話一覧)  : id / vol / file / start / end / lines / chars / chapter / title
TSV(バッチ)  : batch / file / start / end / lines / chars / n_hanashi / range
start/end は 1 始まりの行番号(両端含む)。Read ツールの offset/limit にそのまま使える。
"""
import argparse
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

VOLS = [str(i) for i in range(1, 11)]
RE_H1 = re.compile(r'^#\s+(.*)$')
RE_H2 = re.compile(r'^##\s+(.*)$')


def load(root, vol):
    path = os.path.join(root, vol + '.md')
    with open(path, encoding='utf-8') as f:
        return f.read().split('\n')


def collect(root):
    """全巻を話単位に分解して返す。"""
    rows = []
    for vol in VOLS:
        lines = load(root, vol)
        chapter = ''
        marks = []  # (line_index, title)
        for i, line in enumerate(lines):
            m1 = RE_H1.match(line)
            if m1:
                chapter = m1.group(1).strip()
                continue
            m2 = RE_H2.match(line)
            if m2:
                marks.append((i, chapter, m2.group(1).strip()))
        for n, (i, chap, title) in enumerate(marks):
            end = marks[n + 1][0] - 1 if n + 1 < len(marks) else len(lines) - 1
            body = lines[i:end + 1]
            rows.append({
                'vol': vol,
                'file': vol + '.md',
                'start': i + 1,
                'end': end + 1,
                'lines': end - i + 1,
                'chars': sum(len(x) for x in body),
                'chapter': chap,
                'title': title,
            })
    for n, r in enumerate(rows):
        r['id'] = n + 1
    return rows


def batches(rows, max_lines):
    """話境界を壊さずに、連続行レンジのバッチへまとめる(巻はまたがない)。"""
    out = []
    cur = None
    for r in rows:
        new = (cur is None or cur['file'] != r['file'] or
               cur['lines'] + r['lines'] > max_lines)
        if new:
            cur = {'file': r['file'], 'start': r['start'], 'end': r['end'],
                   'lines': r['lines'], 'chars': r['chars'], 'titles': [r['title']]}
            out.append(cur)
        else:
            cur['end'] = r['end']
            cur['lines'] += r['lines']
            cur['chars'] += r['chars']
            cur['titles'].append(r['title'])
    for n, b in enumerate(out):
        b['batch'] = n + 1
        b['n_hanashi'] = len(b['titles'])
        b['range'] = b['titles'][0] + ' 〜 ' + b['titles'][-1]
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', default='.', help='原稿のあるディレクトリ')
    p.add_argument('--batch', type=int, metavar='MAX_LINES',
                   help='この行数を上限にバッチ化して出力')
    p.add_argument('--json', action='store_true')
    p.add_argument('--summary', action='store_true')
    a = p.parse_args()

    rows = collect(a.root)

    if a.summary:
        chars = sum(r['chars'] for r in rows)
        lines = sum(r['lines'] for r in rows)
        print('話数\t%d' % len(rows))
        print('行数\t%d' % lines)
        print('文字数\t%d' % chars)
        print('概算トークン\t%d' % int(chars * 1.0))
        for vol in VOLS:
            vr = [r for r in rows if r['vol'] == vol]
            print('%s.md\t%d話\t%d行\t%d字' %
                  (vol, len(vr), sum(r['lines'] for r in vr), sum(r['chars'] for r in vr)))
        return

    if a.batch:
        bs = batches(rows, a.batch)
        if a.json:
            print(json.dumps(bs, ensure_ascii=False, indent=1))
            return
        print('batch\tfile\tstart\tend\tlines\tchars\tn_hanashi\trange')
        for b in bs:
            print('%d\t%s\t%d\t%d\t%d\t%d\t%d\t%s' %
                  (b['batch'], b['file'], b['start'], b['end'], b['lines'],
                   b['chars'], b['n_hanashi'], b['range']))
        return

    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return
    print('id\tvol\tfile\tstart\tend\tlines\tchars\tchapter\ttitle')
    for r in rows:
        print('%d\t%s\t%s\t%d\t%d\t%d\t%d\t%s\t%s' %
              (r['id'], r['vol'], r['file'], r['start'], r['end'],
               r['lines'], r['chars'], r['chapter'], r['title']))


if __name__ == '__main__':
    main()
