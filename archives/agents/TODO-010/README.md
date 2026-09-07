# TODO-010 の分担

複数のファイルにまたがり、実装・テスト・文書がまとまって要る項目なので、
**implementer + reviewer + verifier**。挙動が変わらないことを保証したい
リファクタリングで、分岐と条件式が動くため、確認とは別にレビューも入れた。

設計（分割の境界、データクラスの形、`priority` の振り方）は main が
決め、`instructions.md` に書き切ってから渡した。

| 担当 | モデル | 依頼 | 報告 |
|------|--------|------|------|
| implementer | Opus 5（定義の sonnet から上書き） | [instructions.md](instructions.md) | [implementer-report.md](implementer-report.md) |
| reviewer | Opus 5（定義のまま） | [review-instructions.md](review-instructions.md) | [reviewer-report.md](reviewer-report.md) |
| verifier | Sonnet 5（定義の haiku から上書き） | [verify-instructions.md](verify-instructions.md) | [verifier-report.md](verifier-report.md) |

- implementer を Opus 5 に上げたのは、5 ファイル・約 900 行の書き換えで、
  設計を書き切っても「分割前と同じ挙動になる形」を判断する場面が
  多く残ったから
- verifier を Sonnet 5 に上げたのは、チェック項目 5 つと依頼の 7 項目を
  1 つずつ実装に当てて答える必要があったから
- reviewer は挙動が変わらないことの保証が仕事なので、上書きせず Opus 5

`CLAUDE.md` の更新（依頼文の 7）は main が行った。実装担当は
`CLAUDE.md` を触らない決まりのため、依頼文に入れたのが間違いだった。

reviewer の指摘のうち 3 件（読まれない属性の削除、`_display()` への
まとめ、`CLAUDE.md` の記述）は main が直し、verifier に追加で確認させた
（`verifier-report.md` の「追加修正の確認」）。残りは TODO-012 /
TODO-013 / TODO-014 として立てた。

見込みと実施の表、消費トークンの表は
`archives/todo/TODO-010. Timer を分割し、引数をデータクラスにする.md` にある。
