# SPC_gets
## JARL Public Log SCP Generator

JARLコンテストの Public Log を自動収集し、N1MM Logger+ や DXLog などで利用できる Super Check Partial（SCP）ファイルを生成する Python スクリプトです。

外部ライブラリは不要で、Python 3.12 標準ライブラリのみで動作します。

---

# 動作環境

* Python 3.12 以降
* Windows 10 / Windows 11 推奨
* インターネット接続

追加ライブラリのインストールは不要です。

---

# 対応コンテスト

| メニュー | コンテスト       |
| ---- | ----------- |
| j    | ALL JA      |
| 6    | 6m AND DOWN |
| f    | Field Day   |
| a    | 全市全郡（ACAG）  |
| o    | その他         |

---

# インストール

任意のフォルダに以下のファイルを保存してください。

```text
spc_generator_for_JA.py
```

---

# 実行方法

コマンドプロンプトを開き、

```cmd
python spc_generator_for_JA.py
```

または

```cmd
py spc_generator_for_JA.py
```

を実行します。

---

# 起動時メニュー

起動すると以下のメニューが表示されます。

```text
コンテストを選択してください
ALL JA      : j
6m AND DOWN : 6
Field Day   : f
全市全郡     : a
その他       : o
```

生成したいコンテストのキーを入力してください。

---

# 取得対象

以下の Public Log を自動ダウンロードします。

* ALL JA
* 6m AND DOWN
* Field Day
* 全市全郡

現在年から過去5年分を対象とします。

ただし、

```text
2025年未満は取得しません
```

取得した ZIP ファイルは再利用のためキャッシュされます。

---

# キャッシュ

ダウンロードした Public Log は

```text
.jarl_publiclog_cache
```

フォルダへ保存されます。

次回実行時は再ダウンロードせずキャッシュを利用します。

---

# 出力先

## ALL JA

```text
SCP_for_ALLJA
```

## 6m AND DOWN

```text
SCP_for_6D
```

## Field Day

```text
SCP_for_FD
```

## 全市全郡

```text
SCP_for_ACAG
```

## その他

```text
SCP_Files
```

---

# 出力ファイル

## ALL JA

```text
ALLJA_HF.scp
ALLJA_50.scp
```

## 6m AND DOWN

```text
6D_50.scp
6D_VU.scp
6D_1.2.scp
6D_SH.scp
```

## Field Day

```text
FD_HF.scp
FD_50.scp
FD_VU.scp
FD_1.2.scp
FD_SH.scp
```

## 全市全郡

```text
ACAG_HF.scp
ACAG_50.scp
ACAG_VU.scp
ACAG_1.2.scp
ACAG_SH.scp
```

## その他

```text
SCP_Files
└─ Super_Check_file.scp
```

---

# SCPフォーマット

## 通常コンテスト

```text
JA1ZLO     10H
JJ1AHS     12M
JR1ZTT     106H
```

コールサインの後ろにコンテストナンバーが付与されます。

---

## ACAGおよびSH帯

市郡区ナンバーが存在する場合

```text
JA1AAA     100110H
JJ1BBB     1420M
```

市郡区ナンバーが存在しない場合

```text
JA1AAA
JJ1BBB
```

コールサインのみ出力されます。

---

## その他モード

都道府県・地域ナンバーのみを出力します。

パワー区分は除去されます。

例：

Public Log

```text
JA1AAA 10H
JA1BBB 10M
JA1CCC 106L
```

生成結果

```text
JA1AAA     10
JA1BBB     10
JA1CCC     106
```

---

# 対象バンド

## HF

```text
1.8
3.5
7
14
21
28 MHz
```

※ 28MHz は HF として扱います。

## 50

```text
50 MHz
```

## VU

```text
144 MHz
430 MHz
```

## 1.2

```text
1200 MHz
```

## SH

```text
2400 MHz以上
```

---

# 文字コード

ZIP 内のログは以下の順で自動判定します。

1. UTF-8
2. Shift_JIS
3. CP932

---

# エラー処理

以下の場合でも処理を継続します。

* 特定年度の Public Log が存在しない
* ダウンロード失敗
* ZIP ファイル破損
* 文字コード判定失敗

警告メッセージのみ表示されます。

---

# 実行例

```text
コンテストを選択してください
ALL JA      : j
6m AND DOWN : 6
Field Day   : f
全市全郡     : a
その他       : o

> j

ALL JA 用 SCP を生成します。

生成したファイル:
SCP_for_ALLJA\ALLJA_HF.scp
SCP_for_ALLJA\ALLJA_50.scp
```

---

# ライセンス

個人利用・改変自由。

利用によって生じた損害について作者は責任を負いません。
