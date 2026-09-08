# TODO-014 の分担

| 担当 | モデル | 依頼 | 報告 |
|------|--------|------|------|
| implementer | Sonnet 5 | `implementer-task.md` | `implementer-report.md` |
| verifier | Sonnet 5 | `verifier-task.md` | `verifier-report.md` |

決着の記録は
[`archives/todo/TODO-014. pomodoro.py のログと、点滅表示のテストを足す.md`](../../todo/TODO-014.%20pomodoro.py%20のログと、点滅表示のテストを足す.md)。

## この分担にした理由

`pomodoro.py` のログ追加と `tests/test_view.py` のテスト追加で、
2 ファイルにまたがるので執筆は implementer に出した。挙動は変わらない
項目なので reviewer は入れていない。

確認を verifier に分けたのは、「テストが通る」ことと「テストが仕様を
見ている」ことが別だから。実装した本人は自分の書いたテストが通れば
済ませてしまう。点滅の分岐をわざと壊して落ちるかを確かめる手順は
verifier に指示し、その結果、値の文字列をキーにした辞書の脆さも
挙がった（main が受けて直した）。

verifier は定義のモデルが haiku だが、どの行をどう壊すかの判断が要るので
Sonnet 5 に上書きした。
