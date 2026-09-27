# 字型

展開頁的文字使用「源流明體」：內文 EL、篇名 B。已經做成網頁字型檔放在這裡：

- `GenRyuMinTW-EL.woff2`
- `GenRyuMinTW-B.woff2`

這兩個檔案是用 `tools/build_font_subset.py` 從你系統裡「純文字版」的源流明體
（`~/Library/Fonts/GenRyuMin-EL.ttc`、`GenRyuMin-B.ttc`，注意不是 Downloads 裡
`BpmfGenRyuMin` 那份——那份帶注音標示，是給兒童讀物用的版本）抽出網站實際會用到
的字「瘦身」而成，原本各 9MB 縮小到 130 KB 左右，所有訪客都看得到，不需要另外安裝字型。

## 之後新增很多新文字（新字沒被包含進去）

正常情況不用管，網站找不到的字會自動退回「Noto Serif TC」顯示，不會壞掉。
如果想讓新內容也用源流明體，在終端機執行：

```
python3 tools/build_font_subset.py
```

會重新掃過整個網站的文字，重新輸出這兩個檔案。

## 授權

源流明體採用 SIL Open Font License，可以嵌入網站使用，授權全文在這個資料夾裡
（`LICENSE-Gen.txt` 等）。
