# TODO-010 verifier への依頼

リポジトリ `/home/ytani/work/tmr`（ブランチ `develop`）。TODO-010
「`Timer` を分割し、引数をデータクラスにする」が実装されたので確かめる。

**コードは直さないこと。** 結果を報告に書く。

## 読むもの

- 完了条件: `TODO.md` の TODO-010 の節（チェックボックス 5 つ）
- 設計（確定済み）: `archives/agents/TODO-010/instructions.md`
- 実装担当の報告: `archives/agents/TODO-010/implementer-report.md`

## 確かめること

1. `TODO.md` のチェックボックス 5 つが、それぞれ実際に済んでいるか
   （1 つずつ、対応する実装を指して答える）
2. 依頼文の 1〜7 の指示に、やり残しや食い違いが無いか。とくに
   - `Timer` に `t_start` / `t_elapsed` / `is_paused` が残っていないこと
   - `type AlarmParams = tuple[...]` が消えていること
   - CLI のオプションが変わっていないこと
     （`uv run tmr timer --help` と `uv run tmr pomodoro --help` を
     `README.md` の help 出力と見比べる）
   - 分割前にあったテストのケースが、新しい構成のどこかに残っていること
     （`git show HEAD:tests/test_timer.py` と今のテストを突き合わせる）
3. 検証コマンドが通ること。**リポジトリのトップで、この順に流す。**

```bash
uv run pytest tests -q
uv run ruff format --line-length 78 --diff src tests
uv run ruff check --extend-select I src tests
uv run basedpyright src tests
uv run mypy src tests
```

**`mise run` は使わない**（`uv.lock` を作り直してしまう）。
`ruff format` は `--diff` を付けて、差分が出ないことを見ること
（勝手に整形しない）。

4. 実際に動かして、表示が壊れていないこと。この端末は対話できないので、
   疑似端末を使う。

```bash
timeout 20 script -qec "stty rows 24 cols 100; uv run tmr pomodoro -w 0.02 -b 0.02 -l 0.02 -c 2" /dev/null | cat -v | tail -20
```

見るのは、フェーズ名が 16 桁で揃っていること、項目が
date, time, title, limit, rate, elapsed, pbar, remain の順に並ぶこと、
経過率で色が変わること。**できなければ、できなかったと報告に書く**
（想像で書かない）。

## 報告

`archives/agents/TODO-010/verifier-report.md` に、コマンドと結果、
1〜4 の答えを書く。返事は「終わったか・報告ファイルのパス・判断が要る点」
を 5 行以内で。
