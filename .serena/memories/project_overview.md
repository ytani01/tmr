# Project Overview: tmr

`tmr` は、Python 3.13 以上で動作する CLI タイマーおよびポモドーロ・タイマーです。

## 主な機能
- シンプルなカウントダウンタイマー (`tmr timer`)
- ポモドーロ・タイマー (`tmr pomodoro`)
- `blessed` を使用した TUI プログレスバー表示
- ターミナルサイズ変更に追従するレスポンシブな表示
- キー入力による操作（一時停止、進める、戻る等）

## 技術スタック
- **言語:** Python 3.13+
- **プロジェクト管理:** `uv`
- **タスク管理:** `mise`
- **TUI 制御:** `blessed`
- **CLI フレームワーク:** `click`
- **ロギング:** `loguru`
- **静的解析:** `ruff`, `mypy`, `basedpyright`
- **テスト:** `pytest`

## コードベースの構造
- `src/tmr/`: ソースコード
    - `__main__.py`: CLI エントリーポイント
    - `base_timer.py`: タイマーの基底ロジックと TUI 制御
    - `progress_bar.py`: プログレスバーの描画ロジック
    - `click_utils.py`: CLI オプションの共通化など
    - `mylog.py`: loguru の初期化
- `tests/`: テストコード
- `samples/`: サンプルスクリプト
- `docs/`: ドキュメント・画像
