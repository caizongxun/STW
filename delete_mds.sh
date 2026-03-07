#!/bin/bash
# 刪除所有 MD 檔案除了 README.md
find . -maxdepth 1 -name '*.md' ! -name 'README.md' -exec git rm {} \;
