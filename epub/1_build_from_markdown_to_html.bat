@echo off
setlocal

python convert.py -i draft.md -o book.md

pandoc -f markdown+emoji -t html4 --standalone -c ./stylesheet.css book.md title.txt -o book.html --toc --toc-depth=2
