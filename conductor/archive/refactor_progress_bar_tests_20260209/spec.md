# Track Specification - Refactor Progress Bar Tests

## Overview
`src/tmr/progress_bar.py` の単体テストプログラムを再構築します。以前の `test_progress_bar.py` を削除した状態から、より堅牢で網羅的なテストスイートを `pytest` を用いて新規作成します。

## Functional Requirements
- **レンダリング計算の検証**: `get_str` メソッドに対し、様々な進捗率（0%, 25%, 50%, 75%, 100%等）において期待通りのバー文字列が生成されることを検証する。
- **データ駆動テスト**: `pytest.mark.parametrize` を活用し、入力値（`val`, `total`, `bar_len`）と期待値の組み合わせを網羅的にテストする。
- **境界値検証**: 
    - `val=0`, `val=total`
    - `val < 0` (0として扱われるか)
    - `val > total` (100%として維持されるか)
    - `total=0` の場合の安全な挙動
- **レスポンシブ動作の検証**: `bar_len` 引数を動的に変更した場合でも、指定された長さで正確に描画されることを検証する。
- **UI 出力検証**: `display` メソッドが `click.secho` を通じて、指定された色 (`fg`) や属性 (`blink`) で正しく出力されることを `click.testing.CliRunner` または `mock` を用いて検証する。

## Non-Functional Requirements
- **保守性**: テストコードを「正常系」「境界値・異常系」「出力系」のように論理的なクラスまたは関数群に分離する。
- **カバレッジ**: `progress_bar.py` に対して 90% 以上のテストカバレッジを目指す。

## Acceptance Criteria
- 全ての新規テストが `pytest` でパスすること。
- `progress_bar.py` のコードカバレッジが 90% を超えていること。
- `ruff` によるリンターチェックおよび `mypy`, `basedpyright` による型チェックをパスすること。

## Out of Scope
- `ProgressBar` クラス自体のロジック変更（バグが発見された場合の修正は除く）。
- 他のモジュール（`base_timer.py` 等）のテスト作成。
