@echo off
rem grep command is reuquired.
rem Ex: C:\Program Files\Git\usr\bin\grep.exe
rem
rem Caution: save as shift-jis if use Japanese because cmd.exe encoding.

rem s-jis �ł��u�L��v�Ȃǂ����삵�Ȃ��̂Ń_��.

grep -inrE "���܂�|�̂Ƃ�|�Ӎ�|�L��" isemuge*.md
