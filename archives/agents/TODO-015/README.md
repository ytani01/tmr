# TODO-015 の分担

`README.md` と `docs/User.md`, `docs/Developer.md` の整備。
決着の記録は
[archives/todo/TODO-015.](<../../todo/TODO-015. `README.md` と `docs-User.md`, `docs-Developer.md` を整備.md>) にある。

## 誰に何を担当させたか

| 担当 | モデル | 担当したこと | 報告 |
|---|---|---|---|
| main | Opus 5 / high | 3 文書の役割分担、節構成、図 6 枚の設計、`Developer.md` の内容設計 | [design.md](design.md) |
| implementer | Opus 5 / medium | 3 文書の執筆 | [implementer-report.md](implementer-report.md) |
| verifier | Sonnet 5 | 書いたとおりに試せるものの再現、実装との突き合わせ | [verifier-report.md](verifier-report.md) |
| wording | Haiku 4.5 | 日本語の推敲 | [wording-report.md](wording-report.md) |

## その分担にした理由

**文書だけの項目だが、確認を分けた。**
インストール手順・コマンド例・help 出力・画面の表示例は、
書いたとおりに試せる。書いた本人は自分の書いたものを正しいと思って
読み返すので、再現は別の担当に持たせた
（`~/.claude/CLAUDE.md` の TODO-017）。mermaid が実際に描画できるかも
ここで見た。

**reviewer は入れなかった。** 挙動が変わらず、分岐や条件式も動かないため。

**執筆を分けたのは、3 ファイルにまたがるから。**
main は構成と図の設計を持ち、文章そのものは書いていない。

**wording は利用者が明示して依頼した。** 規約上、`.md` を含む項目でも
自動では立てない。

## モデルを上書きした理由

- implementer — 定義は `sonnet`。3 文書 638 行を一度に書き、
  日本語の質が成果物そのものになるので Opus 5 に上げた
- verifier — 定義は `haiku`。表示例 7 行を自力で再現して桁まで
  突き合わせる必要があり、Sonnet 5 に上げた
- wording — 定義のまま（Haiku 4.5）

## 振り返り

分担の振り返りは
[archives/todo/TODO-015.](<../../todo/TODO-015. `README.md` と `docs-User.md`, `docs-Developer.md` を整備.md>)
の「分担の振り返り」にある。要点は 3 つ。

- 同じ表示例の実測を main・implementer・verifier が 3 回やった。
  main が設計の段階で 1 回測って渡せば 2 回減る
- verifier を Sonnet 5 にしたのは正解。料金は全体の 11%
- **wording は verifier より前に通すべきだった。**
  今回は wording が最後なので、その書き換えを verifier が見ていない
