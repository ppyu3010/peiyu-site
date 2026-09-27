#!/bin/bash
# 雙擊這個檔案，就會把 assets 裡的作品和文章整理進網站
cd "$(dirname "$0")"
python3 tools/build-content.py
echo
read -n 1 -s -r -p "按任意鍵關閉視窗…"
