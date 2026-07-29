# -*- coding: utf-8 -*-
# memo/chronology/03-timeline.md を、pandoc で HTML 化しやすい形に整形する。
#
# 03-timeline.md は区画ごとの年表を連結してつくられているため、
#   - 先頭に文書タイトルの h1 がある（title.txt と重複する）
#   - 区間見出しの h1 が二連続している（例: `# 第一週` の直後に `# 第一週 1-1前日 〜 1-10`）
#   - 日付見出しが h3 で、h2 が使われていない
# という状態になっている。これを
#   - 文書タイトルの h1 は削除
#   - 二連続 h1 は先の一つだけ残す
#   - h3 -> h2 に繰り上げ
# へ直し、--toc-depth=2 で「区間 + 日付」の目次が出るようにする。

import os
import re
import sys

def abort(msg):
    print('Error!: {0}'.format(msg))
    exit(1)

def file2list(filepath):
    ret = []
    with open(filepath, encoding='utf8', mode='r') as f:
        ret = [line.rstrip('\n') for line in f.readlines()]
    return ret

def list2file(filepath, ls):
    with open(filepath, encoding='utf8', mode='w') as f:
        f.writelines(['{:}\n'.format(line) for line in ls] )

def parse_arguments():
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument('-i', '--input', default=None,
        help='An input filename.')

    parser.add_argument('-o', '--output', default=None,
        help='An output filename.')

    return parser.parse_args()

RE_H1 = re.compile(r'^# (.+)$')
RE_H3 = re.compile(r'^### (.+)$')

def convert(lines):
    ret = []
    is_title_h1_removed = False
    # 直前に出力した見出しが h1 かどうか。空行はまたいで判定する
    is_previous_heading_h1 = False

    for line in lines:
        m1 = RE_H1.match(line)
        if m1:
            if not is_title_h1_removed:
                # 文書タイトルの h1。title.txt 側と重複するので落とす
                is_title_h1_removed = True
                continue
            if is_previous_heading_h1:
                # 区間見出しの二連続。先に出した方を正とする
                continue
            is_previous_heading_h1 = True
            ret.append(line)
            continue

        m3 = RE_H3.match(line)
        if m3:
            is_previous_heading_h1 = False
            ret.append('## {0}'.format(m3.group(1)))
            continue

        if line.strip() != '':
            is_previous_heading_h1 = False
        ret.append(line)

    return ret

def main(args):
    inputfilepath = args.input
    outputfilepath = args.output

    if inputfilepath is None:
        abort('-i is needed.')
    if outputfilepath is None:
        abort('-o is needed.')
    if not os.path.exists(inputfilepath):
        abort('"{0}" not found.'.format(inputfilepath))

    lines = file2list(inputfilepath)
    list2file(outputfilepath, convert(lines))

    return 0

if __name__ == '__main__':
    args = parse_arguments()
    sys.exit(main(args))
