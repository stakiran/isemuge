# 電子書籍に変換する
- いせむげを Kindle paperwhite で読みたい
- 自分用
- mobi ファイルつくってから、自分の端末に転送すればいいはず

## Requirements
- Pandoc 2.13
- Amazon kindlegen v2.9

## How to write draft.md
- i.md を append する
- i.md の一番最初の見出しを目立たせる
    - 以下は i=2 の場合
        - before: `# 初仕事`
        - after: `# === 第二部　初仕事`
    - 別になくてもいい
    - が、たぶん部の区切りわからなくて少し読みづらい気がする

## How to build on your local
- 1: draft.md を仕上げる
- 2: convert.py で「markdownとして読みやすく表示される形式」に変換
- 3: 2 を pandoc で HTML
    - 表示確認はこれを見る
- 4: 3 の HTML を kindlegen で mobi に変換
    - mobi ファイルは Kindle デスクトップアプリで見れる
    - ファイル名ごとに一つの本しか登録できないので、ビルドし直すたびに端末側データを削除する必要アリ
- 5: 4 の mobi ファイルを Kindle 端末に転送

## How to send to your kindle device2
- https://www.amazon.co.jp/sendtokindle からD&Dで送れる
    - が、処理されるの遅いかも。mobiだと1分で認識されるのにこれだと5分経っても処理が終わらん

アップデートした: [KindleへのMOBIドキュメントの送信に関する最新情報 - stakiran研究所](https://scrapbox.io/sta/Kindle%E3%81%B8%E3%81%AEMOBI%E3%83%89%E3%82%AD%E3%83%A5%E3%83%A1%E3%83%B3%E3%83%88%E3%81%AE%E9%80%81%E4%BF%A1%E3%81%AB%E9%96%A2%E3%81%99%E3%82%8B%E6%9C%80%E6%96%B0%E6%83%85%E5%A0%B1)

## ❌How to send to your kindle device1
with パーソナルドキュメント

- 手順: [Amazon.co.jp ヘルプ: Eメールアドレスを追加しKindleライブラリでドキュメントを受信する](https://www.amazon.co.jp/gp/help/customer/display.html?nodeId=GX9XLEVV8G4DB28H)
- 設定画面: https://www.amazon.co.jp/mn/dcw/myx.html#/home/settings/payment
- [サポート形式](https://www.amazon.co.jp/gp/help/customer/display.html?nodeId=G5WYD9SAF7PGXRNA)
- 要約すると
    - 「このメアドに送れば端末に転送できるよ」的なメアドを登録すればいい
    - mobi, html, docs, pdx
    - epubは対応していない
- 送信方法
    - パーソナルドキュメントメアド宛に、mobiファイル添付して送る
    - 件名は適当に
    - 本文はなしでいい
- Q: paperwhite側に反映されるのはいつ？
    - 2021/03/27 11:36:40 頃試したところ、1分以内に同期された

with ~~PCのKindle側で読み込んだ後、paperwhite側を再起動~~

- やったけど転送されないです

## === 作業メモ

## convert.py 設計
日向で使ったやつ

- before
    - `# 第１部：能ある日向は爪隠す`
    - `# ＝＝　第１章　とある高校生撮り師の日常とその崩壊　＝＝`
    - `# １　フレッシュハンティング`
- after
    - `# 第１部：能ある日向は爪隠す`
    - `## 第１章　とある高校生撮り師の日常とその崩壊`
    - なし

今回

- before
    - `# 転生`
    - `## 第１話　転生`
    - なし

bra

- 前回は部、章まで表示
- 前回は draft.md を整形していた
- 今回は整形なしにしたい

設計

- 話数がついてるので「第n部」みたいな区切り見出しは要らない


