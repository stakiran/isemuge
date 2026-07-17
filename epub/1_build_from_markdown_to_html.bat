@echo off
setlocal

python convert.py -i draft.md -o book.md

pandoc -f markdown+emoji -t html4 --standalone --include-in-header=web_head.html --include-before-body=web_body.html book.md title.txt -o book.html --toc --toc-depth=2
