#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""恒久索引(話ダイジェスト)の構築管理と、そこからの絞り込み。

索引の実体: _yokodan/knowledge/digest/*.jsonl (1行1話)
スキーマ  : .claude/skills/genko-yokodan/reference/digest.md

使い方:
  python idx.py status                        # 進捗と欠番。中断からの再開はこれを見る
  python idx.py plan --per-agent 10           # 未完了分のエージェント割り当て表
  python idx.py merge                         # 断片を digest.jsonl に統合(重複はid新しい方)
  python idx.py view --chars ルナ              # ルナが出る話のダイジェストだけ
  python idx.py view --pair ルナ,タイヨウ       # 両方出る話だけ
  python idx.py view --vol 5,6 --field summary,relations
  python idx.py timeline --pair ルナ,タイヨウ   # 関係の記述だけを時系列で
  python idx.py holes --pair ルナ,タイヨウ      # 両者が出るのに関係記述が無い話(要精読候補)

view / timeline の出力はそのままLLMに読ませる前提。--budget で概算文字数を抑えられる。
"""
import argparse
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manifest import collect  # noqa: E402

DIGEST_DIR = '_yokodan/knowledge/digest'
MERGED = '_yokodan/knowledge/digest.jsonl'


def load_records(root):
    """断片JSONLと統合済みJSONLを両方読み、id -> record にする。"""
    recs = {}
    bad = []
    paths = sorted(glob.glob(os.path.join(root, DIGEST_DIR, '*.jsonl')))
    merged = os.path.join(root, MERGED)
    if os.path.exists(merged):
        paths.insert(0, merged)
    for path in paths:
        with open(path, encoding='utf-8') as f:
            for n, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('//'):
                    continue
                try:
                    r = json.loads(line)
                except ValueError as e:
                    bad.append('%s:%d %s' % (os.path.basename(path), n, e))
                    continue
                if 'id' not in r:
                    bad.append('%s:%d id なし' % (os.path.basename(path), n))
                    continue
                recs[int(r['id'])] = r
    return recs, bad


def names(r, key):
    v = r.get(key) or []
    return [x if isinstance(x, str) else (x.get('name') or '') for x in v]


def rel_lines(r):
    out = []
    for x in r.get('relations') or []:
        if isinstance(x, dict):
            out.append(x)
    return out


def cmd_status(a, rows, recs, bad):
    done = sorted(recs)
    missing = [r['id'] for r in rows if r['id'] not in recs]
    print('全 %d 話 / 済 %d 話 / 未 %d 話  (%.1f%%)' %
          (len(rows), len(done), len(missing), 100.0 * len(done) / len(rows)))
    if bad:
        print('\n[壊れた行 %d 件]' % len(bad))
        for b in bad[:20]:
            print('  ' + b)
    if missing:
        print('\n[未処理の話id]')
        # 連番はレンジで畳む
        span, prev = [], None
        for i in missing:
            if prev is not None and i == prev + 1:
                span[-1][1] = i
            else:
                span.append([i, i])
            prev = i
        print('  ' + ', '.join('%d' % s if s == e else '%d-%d' % (s, e) for s, e in span))
    else:
        print('\n索引は完成しています。')


def cmd_plan(a, rows, recs, bad):
    todo = [r for r in rows if r['id'] not in recs]
    if not todo:
        print('未処理なし。')
        return
    print('# 未処理 %d 話 を %d 話ずつ割り当て → %d エージェント' %
          (len(todo), a.per_agent, (len(todo) + a.per_agent - 1) // a.per_agent))
    print('agent\tfile\tstart\tend\tlines\tchars\tids\ttitles')
    group, n = [], 0
    for r in todo + [None]:
        # 巻をまたいだら切る
        if r is None or (group and (group[-1]['file'] != r['file'] or len(group) >= a.per_agent)):
            n += 1
            print('%d\t%s\t%d\t%d\t%d\t%d\t%s\t%s' % (
                n, group[0]['file'], group[0]['start'], group[-1]['end'],
                group[-1]['end'] - group[0]['start'] + 1,
                sum(g['chars'] for g in group),
                '%d-%d' % (group[0]['id'], group[-1]['id']),
                group[0]['title'] + ' 〜 ' + group[-1]['title']))
            group = []
        if r is not None:
            group.append(r)


def cmd_merge(a, rows, recs, bad):
    path = os.path.join(a.root, MERGED)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    by_id = {r['id']: r for r in rows}
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for i in sorted(recs):
            r = dict(recs[i])
            base = by_id.get(i)
            if base:  # 行番号などの機械的事実は manifest 側で上書きして正とする
                for k in ('vol', 'file', 'start', 'end', 'chapter', 'title'):
                    r[k] = base[k]
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print('%s に %d 話を書き出しました。' % (MERGED, len(recs)))
    if bad:
        print('壊れた行が %d 件ありました。status で確認してください。' % len(bad))


def select(a, rows, recs):
    ids = sorted(recs)
    if a.vol:
        vols = set(v.strip() for v in a.vol.split(','))
        ids = [i for i in ids if str(recs[i].get('vol', '')) in vols]
    if a.chars:
        want = [c.strip() for c in a.chars.split(',')]
        ids = [i for i in ids if any(c in names(recs[i], 'chars') for c in want)]
    if a.pair:
        pa, pb = [c.strip() for c in a.pair.split(',')][:2]
        ids = [i for i in ids
               if pa in names(recs[i], 'chars') and pb in names(recs[i], 'chars')]
    return ids


def cmd_view(a, rows, recs, bad):
    ids = select(a, rows, recs)
    fields = [f.strip() for f in a.field.split(',')] if a.field else None
    used = 0
    for i in ids:
        r = recs[i]
        head = '## [%d] %s %s / %s' % (i, r.get('file', ''), r.get('title', ''),
                                       r.get('chapter', ''))
        body = []
        for k, v in r.items():
            if k in ('id', 'vol', 'file', 'start', 'end', 'chapter', 'title'):
                continue
            if fields and k not in fields:
                continue
            body.append('%s: %s' % (k, json.dumps(v, ensure_ascii=False)))
        block = head + '\n' + '\n'.join(body)
        if a.budget and used + len(block) > a.budget:
            print('\n# --budget %d に達したため打ち切り（該当 %d 話中 表示分まで）' %
                  (a.budget, len(ids)))
            return
        used += len(block)
        print(block + '\n')
    print('# 該当 %d 話 / 概算 %d 字' % (len(ids), used))


def cmd_timeline(a, rows, recs, bad):
    ids = select(a, rows, recs)
    pair = [c.strip() for c in a.pair.split(',')][:2] if a.pair else []
    print('id\tfile\tvol\ttitle\tfrom\tto\tline\tnote')
    n = 0
    for i in ids:
        r = recs[i]
        for x in rel_lines(r):
            fr, to = x.get('from', ''), x.get('to', '')
            if pair and not ({fr, to} & set(pair)):
                continue
            if len(pair) == 2 and {fr, to} != set(pair):
                continue
            n += 1
            print('%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s' %
                  (i, r.get('file', ''), r.get('vol', ''), r.get('title', ''),
                   fr, to, x.get('line', ''), str(x.get('note', '')).replace('\t', ' ')))
    print('\n# %d 話から %d 件' % (len(ids), n))


def cmd_holes(a, rows, recs, bad):
    """両者が同席しているのに関係の記述が無い話。索引の作り漏れ＝要精読候補。"""
    ids = select(a, rows, recs)
    pair = set(c.strip() for c in a.pair.split(',')[:2]) if a.pair else set()
    print('id\tfile\tstart\tend\tchars\ttitle')
    by_id = {r['id']: r for r in rows}
    holes = []
    for i in ids:
        rels = rel_lines(recs[i])
        if pair and any({x.get('from'), x.get('to')} == pair for x in rels):
            continue
        if not pair and rels:
            continue
        if i in by_id:
            holes.append(by_id[i])
    for b in holes:
        print('%d\t%s\t%d\t%d\t%d\t%s' %
              (b['id'], b['file'], b['start'], b['end'], b['chars'], b['title']))
    print('\n# 該当 %d 話中 要精読候補 %d 話 / 概算 %d 字' %
          (len(ids), len(holes), sum(b['chars'] for b in holes)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('cmd', choices=['status', 'plan', 'merge', 'view', 'timeline', 'holes'])
    p.add_argument('--root', default='.')
    p.add_argument('--per-agent', type=int, default=10)
    p.add_argument('--chars', default='', help='この人物が出る話に絞る(カンマ区切りOR)')
    p.add_argument('--pair', default='', help='この2人が両方出る話に絞る 例: ルナ,タイヨウ')
    p.add_argument('--vol', default='', help='巻で絞る 例: 5,6')
    p.add_argument('--field', default='', help='出力するフィールドを限定 例: summary,relations')
    p.add_argument('--budget', type=int, default=0, help='出力の概算文字数上限(0=無制限)')
    a = p.parse_args()

    rows = collect(a.root)
    recs, bad = load_records(a.root)
    # 行番号・巻・話タイトルといった機械的事実は常に manifest 側を正とする。
    # (エージェントが書き落としても view/timeline が出典を出せるように)
    by_id = {r['id']: r for r in rows}
    for i, r in recs.items():
        base = by_id.get(i)
        if base:
            for k in ('vol', 'file', 'start', 'end', 'chapter', 'title'):
                r[k] = base[k]
    if not recs and a.cmd not in ('status', 'plan'):
        sys.exit('索引がまだありません。plan → 走査 → merge の順に進めてください。')
    globals()['cmd_' + a.cmd](a, rows, recs, bad)


if __name__ == '__main__':
    main()
