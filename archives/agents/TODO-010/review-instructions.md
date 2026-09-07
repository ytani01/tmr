# TODO-010 reviewer への依頼

リポジトリ `/home/ytani/work/tmr`（ブランチ `develop`）。TODO-010
「`Timer` を分割し、引数をデータクラスにする」の変更をレビューする。

**コードは直さないこと。** 見つけたことを報告に書く。直すかどうかは
管理者が決める。

## 読むもの

- 設計（確定済み）: `archives/agents/TODO-010/instructions.md`
- 実装担当の報告: `archives/agents/TODO-010/implementer-report.md`
  （「設計から外した点」4 件が書いてある）
- プロジェクトの `CLAUDE.md`（設計とログの規約）
- 変更そのもの: `git diff HEAD` と `git status`（新規ファイルを含む）

## 見てほしいこと

いちばん重要なのは **挙動が変わっていないか**。この項目は
リファクタリングで、画面に出る文字列・キー割り当て・`main()` の
戻り値・項目が削られる順番は今までと同じでなければならない。

1. **`TimerClock`** — 経過・ポーズ・早送り・巻き戻しの式が、分割前の
   `Timer.main()` / `fn_forward()` / `fn_backward()` と同じ結果になるか。
   分割前は `git show HEAD:src/tmr/timer.py` で読める
2. **`TimerView.display()`** — 分割前の `Timer.display()` と、
   同じ入力に対して同じ出力になるか。とくに
   - 幅が足りないときに削られる順番（旧 `COL_PRIORITY` の末尾から `pop`
     ↔ 新 `priority` の昇順）。旧実装との差が出る入力が無いか
   - `pbar` の長さの計算、`state` の点滅条件、経過率による色
   - 実装担当が「省略のループを `while ... pop()` から `for` に変えた」
     と書いている点（旧は空リストへの `pop` で IndexError になり得た）
3. **`Timer`** — フェーズ制御（`main()` が quit のときだけ `True`、
   `next` は `True` を返さない）が保たれているか。ポーズ解除の扱い
   （`fn_quit` / `fn_next` が `clock.is_paused = False` を直接書く形）が
   分割前と同じか
4. **`phases()`** — フェーズの並び・色・秒数・繰り返しが分割前と同じか
5. **設計の良し悪し** — 責務の分け方、`Timer` と `TimerClock` に
   `t_limit` が二重にあること、`TimerTitle.display_text` の置き場所、
   `TimerView` が `title` を `__init__` でしか読まないこと
6. **`CLAUDE.md`**（管理者が直した）の記述が、実装と合っているか
7. ログの規約（`__log = getLogger(__qualname__)` をクラス本体に置く）、
   行長 78 文字、命名や docstring がリポジトリの書き方に揃っているか

テストについても、**分割前にあったケースが新しい構成のどこかで
見られているか**を確かめてほしい（`git show HEAD:tests/test_timer.py`
と、今の `tests/test_timer.py` / `test_view.py` / `test_clock.py` の
突き合わせ）。

## 報告

`archives/agents/TODO-010/reviewer-report.md` に、**重いものから順に**
書く。それぞれ「どこ（ファイル:行）」「何が問題か」「どうなると困るか」。
直したほうがよいものと、好みの範囲のものは分けること。
返事は「終わったか・報告ファイルのパス・判断が要る点」を 5 行以内で。
