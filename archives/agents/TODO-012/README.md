# TODO-012 の分担

決着の記録は
[`archives/todo/TODO-012. 0 分・0 サイクルを指定すると壊れる.md`](../../todo/TODO-012.%200%20分・0%20サイクルを指定すると壊れる.md)。
**2 つの表（見込みと実施、消費トークン）はそちらにある。**

## 分担にした理由

コードの分岐と条件式が変わる項目なので、`~/.claude/CLAUDE.md` に従い、
実装・確認・レビューの 3 つを分けた。

| 担当 | モデル | 役割 |
|---|---|---|
| main | Opus 5 | 再現、方針の決定、境界の設計、各担当への依頼 |
| implementer | Sonnet 5 | 指示された範囲の実装 |
| reviewer | Opus 5（上書き） | 分岐の意味が正しいかのレビュー |
| verifier | Haiku 4.5 | 再現手順とテスト・lint の確認 |

- **reviewer を Opus 5 に上書きした。** 挙動と分岐が変わる項目で、
  「テストが通る」ことと「分岐の意味が正しい」ことは別だから
- **implementer は定義のまま（Sonnet 5 / medium）。** 境界も置き場所も
  main が決めて渡したので、判断の要らない実装になった
- **verifier と reviewer を両方入れた。** 実際、verifier が 4 回とも
  全 PASS を返した同じ差分から、reviewer は 3 回続けて別の穴を見つけている

## やり取り

実装 → レビュー・確認 → 利用者の判断 → 追加実装、を 4 周した。
穴の種類が周回ごとに広がったため。

| 回 | 依頼 | 報告 |
|---|---|---|
| 1 | `implementer-task.md` | `implementer-report.md` / `reviewer-report.md` / `verifier-report.md` |
| 2 | `implementer-task2.md` | `implementer-report2.md` / `reviewer-report2.md` / `verifier-report2.md` |
| 3 | `implementer-task3.md` | `implementer-report3.md` / `reviewer-report3.md` / `verifier-report3.md` |
| 4 | `implementer-task4.md` | `implementer-report4.md` / `reviewer-report4.md` / `verifier-report4.md` |

reviewer と verifier への依頼は `reviewer-task*.md` / `verifier-task*.md`。

**利用者に判断を仰いだのは 4 回。** 0 を弾くか動かすか、レビュー指摘の
どれを取り込むか、`nan` / `inf` を今回直すか、アラームの上限を足すか。
