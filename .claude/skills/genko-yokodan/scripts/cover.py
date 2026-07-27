#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""複数の対象語を「最小の話数」でカバーする話を選ぶ(貪欲法セットカバー)。

「登場キャラ全員の○○を調べる」のように対象がN個ある場合、
全410話を読むのではなく、N個を出現密度高く含む数十話だけを精読すれば足りる。
その数十話を選ぶための道具。

使い方:
  # 30キャラを、それぞれ2話以上カバーするように話を選ぶ
  python cover.py ルナ ユズ アウラ ラウル シキ --per 2

  # 語リストをファイルから(1行1語、# はコメント)
  python cover.py --file targets.txt --per 3 --min-hits 5

出力1: 選ばれた話の一覧(file/start/end 付き。Read の offset/limit にそのまま使う)
出力2: 対象語ごとのカバー状況(何話でカバーされたか。0 のものは要注意)
"""
import argparse
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manifest import collect  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RE_RUBY = re.compile(r'《[^》]*》|｜')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('words', nargs='*')
    p.add_argument('--root', default='.')
    p.add_argument('--file', help='対象語リストのファイル')
    p.add_argument('--per', type=int, default=2, help='1語あたり最低何話カバーするか')
    p.add_argument('--min-hits', type=int, default=3,
                   help='その話でこの回数以上出ていないとカバー扱いしない')
    p.add_argument('--max-hanashi', type=int, default=60, help='選ぶ話数の上限')
    a = p.parse_args()

    words = list(a.words)
    if a.file:
        with open(a.file, encoding='utf-8') as f:
            for line in f:
                line = line.split('#')[0].strip()
                if line:
                    words.append(line)
    words = list(dict.fromkeys(words))
    if not words:
        sys.exit('対象語がありません')

    rows = collect(a.root)
    body = {}
    for vol in sorted(set(r['vol'] for r in rows), key=int):
        with open(a.root + '/' + vol + '.md', encoding='utf-8') as f:
            body[vol] = [RE_RUBY.sub('', x) for x in f.read().split('\n')]

    # 話 -> {語: 出現数}
    counts = []
    for r in rows:
        text = '\n'.join(body[r['vol']][r['start'] - 1:r['end']])
        c = {w: text.count(w) for w in words}
        c = {w: n for w, n in c.items() if n >= a.min_hits}
        counts.append(c)

    need = {w: a.per for w in words}
    chosen = []
    used = set()
    while any(v > 0 for v in need.values()) and len(chosen) < a.max_hanashi:
        best, best_score = None, 0
        for i, c in enumerate(counts):
            if i in used:
                continue
            score = sum(min(1, need[w]) * min(n, 20) for w, n in c.items() if need[w] > 0)
            if score > best_score:
                best, best_score = i, score
        if best is None:
            break
        used.add(best)
        chosen.append(best)
        for w in counts[best]:
            if need[w] > 0:
                need[w] -= 1

    chosen.sort()
    total_chars = sum(rows[i]['chars'] for i in chosen)
    print('# 選定話 %d 話 / 全 %d 話  概算 %d 字 (全文の %.1f%%)' %
          (len(chosen), len(rows), total_chars,
           100.0 * total_chars / sum(r['chars'] for r in rows)))
    print('id\tfile\tstart\tend\tchars\ttitle\tcovers')
    for i in chosen:
        r = rows[i]
        covers = ','.join('%s(%d)' % (w, n) for w, n in
                          sorted(counts[i].items(), key=lambda x: -x[1]))
        print('%d\t%s\t%d\t%d\t%d\t%s\t%s' %
              (r['id'], r['file'], r['start'], r['end'], r['chars'], r['title'], covers))

    print('\n# カバー状況 (残 = まだ足りない話数)')
    covered = defaultdict(int)
    for i in chosen:
        for w in counts[i]:
            covered[w] += 1
    for w in words:
        mark = '' if need[w] == 0 else '  <-- 不足'
        print('%s\t%d話\t残%d%s' % (w, covered[w], need[w], mark))


if __name__ == '__main__':
    main()
