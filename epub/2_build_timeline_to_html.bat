@echo off
setlocal

python timeline_convert.py -i ..\memo\chronology\03-timeline.md -o timeline.md

pandoc -f markdown+emoji -t html5 --standalone --include-in-header=web_head.html --include-in-header=timeline_head.html --include-before-body=timeline_body.html timeline.md timeline_title.txt -o ..\docs\timeline.html --toc --toc-depth=2
