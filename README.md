# tmr -- ポモドーロタイマー

ターミナル上で動作する、効率的でカスタマイズ可能なポモドーロ・タイマーです。
Richライブラリを使用した美しいTUI（Text User Interface）と、デスクトップ通知機能を備えています。

## 特徴
- **TUIによる進捗表示**: プログレスバーで残り時間を視覚的に把握できます。
- **カスタマイズ可能**: 作業時間、休憩時間、サイクル数を自由に変更できます。
- **デスクトップ通知**: セッション終了時に通知（`notify-send`等）を送り、ユーザーの確認を待ちます。
- **カラーテーマ**: 作業中は赤、休憩中は緑と、状態に合わせて色が変化します。

## インストール方法

`uv` を使用してインストールすることをお勧めします。

```bash
# クローンしてインストール
git clone https://github.com/ytani/tmr.git
cd tmr
uv sync
```

## 使い方

### 基本的な実行
デフォルト設定（作業25分、休憩5分、4サイクル）で開始します。

```bash
uv run tmr pomodoro
```

### オプションの指定
作業時間を15分、休憩時間を3分に設定して実行する例：

```bash
uv run tmr p --work-time 15 --break-time 3
```

### ヘルプ
すべてのオプションを確認するには `-h` または `--help` を使用します。

```
$ uv run tmr p --help
Usage: tmr [OPTIONS]

Options:
  -w, --work-time INTEGER        working time  [default: 25]
  -b, --break-time INTEGER       break time  [default: 5]
  -l, --long-break-time INTEGER  long break time  [default: 5]
  -c, --cycles INTEGER           cycles  [default: 4]
  -V, -v, --version              Show the version and exit.
  -d, --debug                    debug flag
  -h, --help                     Show this message and exit.
```

## ビジュアル (TUI)
実行すると、以下のようなリッチな画面が表示されます。

- **Header**: 現在のサイクル数（例: `Cycle: 1/4`）とセッション状態を表示。
- **Progress Bar**: 残り時間と進捗率（%）をリアルタイムで更新。
- **Notifications**: セッション終了時にデスクトップ通知が表示され、キー入力待ち状態になります。

---
(c) 2026 Yoichi Tanibayashi
