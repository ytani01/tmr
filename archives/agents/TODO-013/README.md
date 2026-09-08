# TODO-013 の分担

| 担当 | 報告 |
|------|------|
| main（実装） | — |
| verifier | [verifier-report.md](verifier-report.md) |
| reviewer | [reviewer-report.md](reviewer-report.md) |

## この分担にした理由

立てたときの見込みは `implementer + reviewer + verifier` だったが、
**着手して差分の見当がついた時点で、実装を main が持つ形に見込みの行を
書き直した**（`TODO.md` の該当節を、着手時に 1 行だけ変更した）。
理由は、変更が `progress_bar.py` / `view.py` / `timer.py` の 3 ファイル・
20 行程度に収まると分かったため。依頼文を書いて報告を読む往復のほうが
高くつく規模だった。

確認とレビューは分けた。挙動そのものは変わらないが、
`rate = val / total` と `if val >= total or stop:` の 2 箇所で参照元が
`self.total` から引数に変わるので、`~/.claude/CLAUDE.md` の
「挙動が変わる項目、分岐や条件式が変わる項目には、確認の担当とは別に
レビューの担当も入れる」に当たる。

モデルは、verifier を定義の haiku から Sonnet 5 に上書きした
（追加したテストが意味を持つかの判断が要るため）。reviewer は定義のまま
Sonnet 5 / effort high（見る範囲が狭いので上書きしなかった）。

振り返りは
`archives/todo/TODO-013. ProgressBar が古い t_limit を持ち続ける.md` にある。
