# Track Specification: expand_unit_tests

## Overview
`ProgressBar` クラスを中心とした単体テストの拡充を行い、ロジックの正当性と堅牢性を担保する。特に先日実施した `total=0` のガード（ゼロ除算対策）が正しく機能していることを自動テストで検証する。

## Functional Requirements
- `ProgressBar.get_str()` メソッドのテスト。
    - 正常系: 任意の `total`, `val`, `bar_len` に対して、期待通りのバー文字列が生成されること。
    - 異常系/境界値: `total=0` の時に 100% 表示（あるいはエラーにならないこと）を確認。
    - 異常系/境界値: `val > total` や `val < 0` の場合に、バーの長さが範囲内に収まること。
- `pytest.mark.parametrize` を活用し、複数のテストケース（異なる値の組み合わせ）を網羅的にテストする。

## Non-Functional Requirements
- 特になし（既存の `pytest` 環境に従う）。

## Acceptance Criteria
- [ ] `tests/test_progress_bar.py` が新規作成される。
- [ ] `total=0` を含むすべてのテストケースがパスする。
- [ ] `mise run test` を実行して、既存の `tests/test_dummy.py` と合わせてすべてのテストが成功する。

## Out of Scope
- `BaseTimer` や CLI コマンド自体のテスト（今回は `ProgressBar` に集中する）。
- TUI の物理的な表示テスト（文字列生成ロジックのテストに留める）。
