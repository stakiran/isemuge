#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""全原稿から候補語を機械抽出する(LLMトークン0)。

「全巻に出てくる○○を全部」系のタスクで、まず母集団を機械的に作るための道具。
高再現率(取りこぼさない)が目的なのでノイズは混ざる。絞り込みはLLM側でやる。

使い方:
  python vocab.py kata --min 10 --vols 2      # カタカナ語(人名/地名/固有名詞の候補)
  python vocab.py kanji --min 30              # 漢字熟語
  python vocab.py ruby --min 3                # ルビ《》つき語(造語/固有名詞が集中する)
  python vocab.py word 俺 私 僕 あたし        # 指定語の出現統計(一人称調査などに)
  python vocab.py serifu --min 5              # 「」冒頭の呼びかけ語

出力TSV: word / total / vols / vol_hits / first
  total    : 全巻での出現回数
  vols     : 出現した巻数(1〜10)。「複数の話に登場」判定の一次フィルタ
  vol_hits : 巻ごとの出現回数 1:12,2:5,...
  first    : 初出 file:line
"""
import argparse
import re
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

VOLS = [str(i) for i in range(1, 11)]

RE_RUBY = re.compile(r'《([^》]*)》')
RE_RUBY_BASE = re.compile(r'｜([^《]+)《([^》]*)》')
RE_KATA = re.compile(r'[ァ-ヴー・]{2,}')
RE_KANJI = re.compile(r'[一-龠]{2,}')
RE_SERIFU_HEAD = re.compile(r'^「([^、。！？…\s」]{2,8})[、。！？…]')

# 明らかに人名でない頻出カタカナ語。除外ではなく参考用(--stop で除外)。
STOP_KATA = set('''
コイツ アイツ ソイツ ドイツ オレ ボク ワタシ アタシ ワシ
モンスター ゲーム レベル スキル ステータス パーティー ダンジョン
クソ ニヤ ゾク ドキ ガチ ヤバ ハハ フフ ワハハ ニヤニヤ
'''.split())


def read_vol(root, vol, strip_ruby=True):
    with open(root + '/' + vol + '.md', encoding='utf-8') as f:
        lines = f.read().split('\n')
    if strip_ruby:
        lines = [RE_RUBY.sub('', x) for x in lines]
    return lines


def tally(root, extract, strip_ruby=True):
    total = Counter()
    per_vol = defaultdict(Counter)
    first = {}
    for vol in VOLS:
        for i, line in enumerate(read_vol(root, vol, strip_ruby)):
            for w in extract(line):
                total[w] += 1
                per_vol[w][vol] += 1
                first.setdefault(w, '%s.md:%d' % (vol, i + 1))
    return total, per_vol, first


def emit(total, per_vol, first, min_count, min_vols, stop):
    print('word\ttotal\tvols\tvol_hits\tfirst')
    rows = []
    for w, c in total.items():
        if stop and w in STOP_KATA:
            continue
        nv = len(per_vol[w])
        if c < min_count or nv < min_vols:
            continue
        rows.append((c, nv, w))
    rows.sort(key=lambda x: (-x[0], x[2]))
    for c, nv, w in rows:
        hits = ','.join('%s:%d' % (v, per_vol[w][v]) for v in VOLS if per_vol[w][v])
        print('%s\t%d\t%d\t%s\t%s' % (w, c, nv, hits, first[w]))
    print('# %d 語' % len(rows), file=sys.stderr)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['kata', 'kanji', 'ruby', 'word', 'serifu'])
    p.add_argument('words', nargs='*', help='mode=word のときの調査対象語')
    p.add_argument('--root', default='.')
    p.add_argument('--min', type=int, default=1, help='最小出現回数')
    p.add_argument('--vols', type=int, default=1, help='最小出現巻数')
    p.add_argument('--stop', action='store_true', help='既知の非人名カタカナ語を除外')
    a = p.parse_args()

    if a.mode == 'kata':
        t, v, f = tally(a.root, lambda s: RE_KATA.findall(s))
    elif a.mode == 'kanji':
        t, v, f = tally(a.root, lambda s: RE_KANJI.findall(s))
    elif a.mode == 'ruby':
        def ex(s):
            out = ['%s《%s》' % (b, r) for b, r in RE_RUBY_BASE.findall(s)]
            return out or ['《%s》' % r for r in RE_RUBY.findall(s)]
        t, v, f = tally(a.root, ex, strip_ruby=False)
    elif a.mode == 'serifu':
        def ex(s):
            m = RE_SERIFU_HEAD.match(s)
            return [m.group(1)] if m else []
        t, v, f = tally(a.root, ex)
    else:
        if not a.words:
            sys.exit('mode=word には調査対象語が必要です')
        ws = a.words
        t, v, f = tally(a.root, lambda s: [w for w in ws if w in s])

    emit(t, v, f, a.min, a.vols, a.stop)


if __name__ == '__main__':
    main()
