# Workflow: tmr

## Development Cycle
1. **Feature/Bugfix**: 新機能やバグ修正ごとにブランチを作成（推奨）。
2. **Lint/Type Check**: `mise run lint` を実行し、Ruff と Mypy のエラーがないことを確認。
3. **Test**: `mise run test` (pytest) を実行し、すべてのテストがパスすることを確認。
4. **Build**: `mise run build` でパッケージをビルド。

## Coding Standards
- **Line Length**: 78文字以内 (Ruff 設定を遵守)。
- **Docstrings**: すべてのパブリックな関数、クラス、メソッドに Google スタイルまたは NumPy スタイルの docstring を付与。
- **Type Hints**: すべての関数定義で型ヒントを必須とする。

## Testing Policy
- 新機能には必ず単体テスト (`tests/` 配下) を追加する。
- 既存の挙動を壊していないか、リファクタリングの際も `mise run test` で検証する。

## CI/CD (Future)
- GitHub Actions を利用した自動テストとリンターチェック。
- PyPI への自動リリース。
