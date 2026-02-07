# Implementation Plan: expand_unit_tests

## Phase 1: Test Environment Setup & Infrastructure
- [x] Task: テストファイルの新規作成
    - [x] `tests/test_progress_bar.py` を作成する。
    - [x] `ProgressBar` クラスをインポートし、最小限のテスト（インスタンス化テストなど）を記述する。

## Phase 2: Implement Unit Tests for ProgressBar
- [x] Task: 正常系のテストケース実装
    - [x] `pytest.mark.parametrize` を使用し、標準的な `total`, `val` の組み合わせ（0%, 50%, 100%など）をテストする。
- [x] Task: 境界値・異常系のテストケース実装
    - [x] `total=0` のケースを追加し、ゼロ除算が発生しないことを検証する。
    - [x] `val > total` や `val < 0` のケースを追加し、バーの長さが適切に制限されることを検証する。
- [x] Task: カスタム表示のテストケース実装
    - [x] `bar_len` や `ch_on`, `ch_off` を変更した際に出力が正しく反映されるか検証する。

## Phase 3: Verification & Quality Assurance
- [x] Task: テストの実行と修正
    - [x] `uv run pytest tests/test_progress_bar.py` を実行し、すべてのテストがパスすることを確認する。
- [x] Task: 全体的な品質チェック
    - [x] `mise run lint` を実行し、テストコードがコーディング規約に準拠しているか確認する。
    - [x] `mise run test` を実行し、全テストがパスすることを確認する。
