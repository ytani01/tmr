# TODO-018 verifier への依頼

## 目的

サブエージェントの定義ファイルの変更が、指示どおりか、他の記述と
矛盾していないかを確かめる。**`tmr` のコードは変えていない。**

## 対象範囲

`~/.claude` リポジトリ（`tmr` とは別の git リポジトリ）の 3 ファイル。

- `~/.claude/agents/verifier.md`
- `~/.claude/agents/reviewer.md`
- `~/.claude/CLAUDE.md`

`~/.claude` で `git diff` を取ること（`tmr` 側の `git diff` には出ない）。

## 指示の内容（`~/work/tmr/TODO.md` の TODO-018）

1. `agents/verifier.md` の既定モデルを `sonnet` にし、`effort: medium` を足す
2. `agents/verifier.md` の「やること」に、実際に効いた確かめ方を例として足す
3. `agents/reviewer.md` に「事前レビュー」の役割を足す
4. `CLAUDE.md` に、子プロセスを扱う項目の確認を 1 行足す

背景と「決まっていること」「注意」は `~/work/tmr/TODO.md` の TODO-018 の
節にある。**先に読むこと。**

## 確かめてほしいこと

1. **4 項目それぞれが実際に入っているか。** 差分の該当箇所を引用する
2. **frontmatter が壊れていないか。** `verifier.md` の YAML が他の
   定義ファイル（`implementer.md` / `reviewer.md`）と同じ形か。
   `effort` に使える値は `low` / `medium` / `high` / `xhigh` / `max`
3. **3 ファイルの間で矛盾していないか。** 特に次の 3 点:
   - `verifier.md` に足した確かめ方の例が、`reviewer.md` の担当範囲
     （壊れ方を探す）を侵していないか。TODO-018 の背景 2 は
     「壊れ方を探すのは reviewer のまま」と決めている
   - `reviewer.md` の「事前レビュー」が、`verifier.md` の役割と
     重なっていないか
   - `CLAUDE.md` に足した 1 行が、既存の記述と重複・矛盾していないか
4. **`CLAUDE.md` の規約を定義ファイルへ書き写していないか。**
   `~/.claude/skills/todo-workflow/SKILL.md` の「サブエージェントの定義」に
   ある禁止事項（規約を写すと 2 箇所でドリフトする）
5. **`tmr` 側のファイルが変わっていないか。** `~/work/tmr` で
   `git status` を取り、`TODO.md` と `archives/` 以外が変わっていないこと
6. **引用した TODO 番号（tmr の TODO-009 / 013 / 014 / 016 / 017）が
   実際にその内容か。** `~/work/tmr/archives/todo/` の該当ファイルの
   「分担の振り返り」と突き合わせる

## 完了条件

上の 6 点それぞれについて、確かめた結果と根拠が報告に書かれている。

## やらないこと

- **何も直さない。** 見つけたことは報告するだけ
- コミットしない
- 定義ファイルが「次のセッションから効く」ことの確認は不要
  （Claude Code の再起動は利用者が行う）

## 報告

`~/work/tmr/archives/agents/TODO-018/verifier-report.md` に書く。
返事は 5 行以内。
