# TODO-014 確認依頼（verifier）

リポジトリ: /home/ytani/work/tmr（branch: develop、未コミットの差分が対象）

**コードは直さないこと。** 見つけたことは報告するだけにする。

## 対象

`git diff`（`src/tmr/pomodoro.py` と `tests/test_view.py`）。
実装者の報告は `archives/agents/TODO-014/implementer-report.md`。
項目の内容は `TODO.md` の TODO-014。

## 確かめること

1. **ログが `CLAUDE.md` の「ログ」の節どおりか。**
   `PomodoroTimer` にクラス本体の `__log = getLogger(__qualname__)` が
   あること、`phases()` はモジュール先頭の `_log` を使っていること。
   書き方が `src/tmr/clock.py` と揃っているか
2. **足したテストが、点滅の仕様を実際に捕まえるか。**
   `src/tmr/view.py` の点滅の分岐（`pause_blink` の列、`state` 列の
   `is_timeup`）を**わざと壊して**（例: `f_blink = True` の行を消す）、
   足したテストが落ちることを確かめる。落ちなければテストが仕様を
   見ていない。確かめたら**必ず元に戻す**（`git checkout` ではなく
   編集を戻す。他の未コミットの差分を消さないこと）
3. **テストの書き方の穴。**
   `test_display_pause_blink` / `test_display_timeup_blink` は
   `click.style` の呼び出しを「値の文字列」をキーにした dict にして
   いる。複数の列が同じ値の文字列になったときに取り違えないか、
   その懸念が実際に問題になるかを見る
4. **既存のテストと重複していないか**（`test_display_pause_state` /
   `test_display_timeup_state` と役割が分かれているか）
5. 下がすべて通ること。

```bash
uv run pytest tests
uv run ruff format --check --line-length 78 src tests
uv run ruff check --extend-select I src tests
uv run basedpyright src tests
uv run mypy src tests
```

## 報告

`archives/agents/TODO-014/verifier-report.md` に、確かめた手順と結果、
残る懸念を書く。2 で壊して落ちたことの実際の出力（要点）を残すこと。
返事は「終わったか・報告ファイルのパス・判断が要る点」の 5 行以内。
