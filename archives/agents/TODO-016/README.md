# TODO-016 の分担

## 分担にした理由

`timer.py` / `cli.py` / `pomodoro.py` の 3 ファイルにまたがり、
実装とテストと文書がまとまって要るので、実装の担当も分けた。
**アラームの分岐（ビープか外部コマンドか）と、キー入力待ちを抜ける条件が
変わる**ので、確認とは別にレビューの担当も入れた
（テストが通ることを見ても、分岐の意味が変わったことは捕まえられない）。

| 担当 | 役割 |
|------|------|
| implementer | 実装とテスト、文書の修正 |
| verifier | 指示どおりか、テスト・lint が通るかの確認 |
| reviewer | 分岐と設計・規約に照らしたレビュー |

## 報告

- [implementer-report.md](implementer-report.md)
- [verifier-report.md](verifier-report.md)
- [reviewer-report.md](reviewer-report.md)
