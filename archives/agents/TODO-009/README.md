# TODO-009 の分担

移動と改名だけで挙動が変わらない項目なので、**implementer + verifier**。
分岐や条件式が変わらないため reviewer は入れていない
（`~/.claude/CLAUDE.md`「挙動が変わる項目には…レビューの担当も入れる」の
裏返し）。

| 担当 | モデル | 依頼 | 報告 |
|------|--------|------|------|
| implementer | Sonnet 5（定義のまま） | [instructions.md](instructions.md) | [implementer-report.md](implementer-report.md) |
| verifier | Sonnet 5（定義の haiku から上書き） | [verify-instructions.md](verify-instructions.md) | [verifier-report.md](verifier-report.md) |

- implementer を上書きしなかったのは、依頼文に手順を書き切ったので
  判断が残らなかったから
- verifier を Sonnet 5 に上げたのは、照合する項目が多く、
  「旧ファイルと機械置換 diff を取る」ような手順を自分で組み立てる
  必要があったから

見込みと実施の表、消費トークンの表は
`archives/todo/TODO-009. モジュール構成を整理する（移動と改名だけ）.md` にある。
