#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""全原稿から「該当箇所だけ」を文脈つきで抜き出す(LLMトークンを本文の1/1000に圧縮)。

全文を読ませる代わりに、判断に必要な数十箇所だけを渡すための道具。
--spread により全10巻に散らしてサンプリングするので、
「1巻だけ見て結論を出す」事故を防げる。

使い方:
  # 出現分布だけ見る(どの話にいるか)
  python ctx.py ユズ --count

  # 前後2行つきで全巻から30件サンプリング
  python ctx.py ユズ -B2 -A2 --max 30

  # ユズの近くにある一人称つきセリフだけを抜く(話者推定用)
  python ctx.py "^「.*(俺|私|僕|わたし|あたし|ワシ)" --regex --near ユズ --nw 4 --max 25

  # 特定巻に限定
  python ctx.py フレア --vol 7,8 --max 20

出力は `--- 8.md:1234 [第300話 タイトル]` のヘッダ + 本文行。
末尾に総ヒット数と、サンプリングで落とした件数を必ず出す(取りこぼしの自覚用)。
"""
import argparse
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

VOLS = [str(i) for i in range(1, 11)]
RE_H2 = re.compile(r'^##\s+(.*)$')
RE_RUBY = re.compile(r'《[^》]*》|｜')


def load(root, vol, strip_ruby):
    with open(root + '/' + vol + '.md', encoding='utf-8') as f:
        lines = f.read().split('\n')
    titles = []
    cur = '(冒頭)'
    for line in lines:
        m = RE_H2.match(line)
        if m:
            cur = m.group(1).strip()
        titles.append(cur)
    if strip_ruby:
        lines = [RE_RUBY.sub('', x) for x in lines]
    return lines, titles


def main():
    p = argparse.ArgumentParser()
    p.add_argument('pattern')
    p.add_argument('--root', default='.')
    p.add_argument('--regex', action='store_true', help='pattern を正規表現として扱う')
    p.add_argument('-B', '--before', type=int, default=0)
    p.add_argument('-A', '--after', type=int, default=0)
    p.add_argument('--max', type=int, default=40, help='出力する最大件数(0で無制限)')
    p.add_argument('--spread', action='store_true', default=True,
                   help='全巻に均等に散らしてサンプリング(既定ON)')
    p.add_argument('--head', dest='spread', action='store_false',
                   help='先頭から順に出す')
    p.add_argument('--vol', default='', help='対象巻をカンマ区切りで限定 例: 7,8')
    p.add_argument('--near', default='', help='この語が近傍にある箇所だけに絞る')
    p.add_argument('--nw', type=int, default=3, help='--near の近傍行数')
    p.add_argument('--count', action='store_true', help='話ごとのヒット数だけ出す')
    p.add_argument('--keep-ruby', action='store_true', help='ルビ《》を除去しない')
    a = p.parse_args()

    rx = re.compile(a.pattern) if a.regex else None
    vols = [v.strip() for v in a.vol.split(',') if v.strip()] or VOLS

    hits = []       # (vol, line_no(1始まり), title)
    per_hanashi = {}
    order = []
    for vol in vols:
        lines, titles = load(a.root, vol, not a.keep_ruby)
        for i, line in enumerate(lines):
            ok = rx.search(line) if rx else (a.pattern in line)
            if not ok:
                continue
            if a.near:
                lo, hi = max(0, i - a.nw), min(len(lines), i + a.nw + 1)
                if not any(a.near in x for x in lines[lo:hi]):
                    continue
            key = (vol, titles[i])
            if key not in per_hanashi:
                per_hanashi[key] = 0
                order.append(key)
            per_hanashi[key] += 1
            hits.append((vol, i, titles[i], lines))

    if a.count:
        print('vol\thits\ttitle')
        for vol, title in order:
            print('%s\t%d\t%s' % (vol, per_hanashi[(vol, title)], title))
        print('\n総ヒット %d 件 / %d 話 / %d 巻' %
              (len(hits), len(order), len(set(v for v, _ in order))))
        return

    picked = hits
    if a.max and len(hits) > a.max:
        if a.spread:
            step = len(hits) / float(a.max)
            picked = [hits[int(n * step)] for n in range(a.max)]
        else:
            picked = hits[:a.max]

    for vol, i, title, lines in picked:
        lo, hi = max(0, i - a.before), min(len(lines), i + a.after + 1)
        print('--- %s.md:%d [%s]' % (vol, i + 1, title))
        for x in lines[lo:hi]:
            if x.strip():
                print(x)
        print('')

    print('=== 総ヒット %d 件 / %d 話。出力 %d 件（%d 件は未出力）' %
          (len(hits), len(order), len(picked), len(hits) - len(picked)))


if __name__ == '__main__':
    main()
