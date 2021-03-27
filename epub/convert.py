# -*- coding: utf-8 -*-

import os
import re
import sys

def abort(msg):
    print('Error!: {0}'.format(msg))
    exit(1)

def get_filename(path):
    return os.path.basename(path)

def get_basename(path):
    return os.path.splitext(get_filename(path))[0]

def get_extension(path):
    return os.path.splitext(get_filename(path))[1]

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

    args = parser.parse_args()
    return args

def get_converted_lines(lines):
    new_lines = []

    count_blankline_continuous = 0
    is_prev_line_section = False

    for i,line in enumerate(lines):
        is_sentence_line = False
        is_section_line = False
        is_blank_line = False
        is_eol = False

        if i == len(lines)-1:
            is_eol = True

        if len(line.strip())==0:
            is_blank_line = True
        elif line[0] == '#':
            is_section_line = True
        else:
            is_sentence_line = True

        if is_sentence_line and count_blankline_continuous==0:
            if not(is_prev_line_section):
                new_lines.append('')
            new_lines.append(line)
            # update state
            # -> nothing
            continue

        if is_sentence_line and count_blankline_continuous!=0:
            new_lines.append('')
            new_lines.append('<br>'*count_blankline_continuous)
            new_lines.append('')
            new_lines.append(line)
            # update state
            count_blankline_continuous = 0
            is_prev_line_section = False
            continue

        if is_blank_line:
            # update state
            count_blankline_continuous += 1
            is_prev_line_section = False
            continue

        if is_section_line:
            new_lines.append('')
            new_lines.append('<div style="page-break-before:always"></div>')
            new_lines.append('')
            new_lines.append(line)
            # update state
            count_blankline_continuous = 0
            is_prev_line_section = True
            continue

        raise RuntimeError('ここには来ないはずだが')

    return new_lines

def get_subsectionized_lines(lines):
    new_lines = []

    for i,line in enumerate(lines):
        if len(line.strip())==0 or line[0] != '#':
            new_lines.append(line)
            continue

        # [見出し構造]
        #
        # # プロローグ
        # ## 展開
        # # 転生
        # ## 第１話　転生
        # ## 第２話　理不尽
        # ...
        #
        # - 既に読みやすく整ってるのでいじらない
        # - 話数がついてるので「第n部」みたいな区切り見出しも入れない


        new_lines.append(line)

    return new_lines

def ____main____():
    pass

if __name__ == "__main__":
    args = parse_arguments()

    MYDIR = os.path.abspath(os.path.dirname(__file__))
    infilepath  = args.input
    outfilepath = args.output
    if infilepath == None:
        abort('An input filepath required!')
    if outfilepath == None:
        abort('An output filepath required!')

    if not(os.path.exists(infilepath)):
        abort('The input file "{0}" does not exists.'.format(infilepath))

    lines = file2list(infilepath)

    new_lines = get_subsectionized_lines(lines)

    lines = new_lines
    new_lines = get_converted_lines(lines)

    list2file(outfilepath, new_lines)
