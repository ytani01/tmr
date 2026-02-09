# Suggested Commands

このプロジェクトで頻繁に使用されるコマンドです。`uv` と `mise` を前提としています。

## アプリケーションの実行
- `uv run tmr --help`: 全体ヘルプの表示
- `uv run tmr timer <minutes>`: 指定分数のタイマー起動
- `uv run tmr pomodoro`: ポモドーロ・タイマーの起動

## 開発・メンテナンス
- `mise run uppj`: プロジェクトの依存関係を更新し、編集モードでインストールする
- `mise run lint`: `ruff` (format & check), `basedpyright`, `mypy` を一括実行する
- `mise run test`: `pytest` によるテストを実行する（`lint` に依存）
- `mise run build`: パッケージをビルドする（`test` に依存）

## Git 操作
- 標準的な `git` コマンドを使用してください。
- `git status`, `git diff`, `git log` など。
