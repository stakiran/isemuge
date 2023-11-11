@echo off
setlocal

python convert.py -i draft.md -o book.md

pandoc -f markdown+emoji -t epub3 book.md title.txt -o book.epub -c ./stylesheet.css  --toc --toc-depth=2 --epub-cover-image=cover.jpg --template=template.epub3

