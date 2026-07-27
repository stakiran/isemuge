@echo off
rem grep command is reuquired.
rem Ex: C:\Program Files\Git\usr\bin\grep.exe
rem
rem Caution: save as shift-jis if use Japanese because cmd.exe encoding.

rem s-jis でも「有難」などが動作しないのでダメ.

grep -inrE "ごまか|のとき|胡座|有難" isemuge*.md
