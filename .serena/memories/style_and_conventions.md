# Style and Conventions

## 基本ルール
- **1行の長さ:** 最大 78 文字 (`ruff` の設定に準拠)。
- **ヘッダー:** すべてのソースファイルとテストファイルの冒頭に以下の著作権表示を含める必要があります。
  ```python
  #
  # (c) 2026 Yoichi Tanibayashi
  #
  ```
- **インポート順序:** `ruff` の `I` (isort) ルールに従ってソートする。
- **命名規則:**
    - クラス名: `PascalCase`
    - 関数・変数・モジュール名: `snake_case`

## 静的解析と型
- **型ヒント:** 全ての関数とメソッドに適切な型ヒントを付与する。
- **Docstrings:** トリプルダブルクォート (`"""Docstring."""`) を使用し、簡潔に記述する。
- **静的解析ツール:** `ruff`, `mypy`, `basedpyright` をパスする必要がある。

## TUI 制御
- `blessed.Terminal` を使用し、エスケープシーケンスを直接扱う場合は `src/tmr/__init__.py` で定義された定数（`ESQ_EL2`, `ESQ_CSR_OFF` 等）を使用する。
