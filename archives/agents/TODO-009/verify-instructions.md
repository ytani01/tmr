# TODO-009 確認依頼（verifier）

実装は済んでいる（未コミット）。**直さないこと。** 見つけたことは報告する。

## 依頼の中身

`archives/agents/TODO-009/instructions.md` に実装への指示がある。
実装の報告は `archives/agents/TODO-009/implementer-report.md`。
両方読んでから確かめること。

## 確かめること

1. **検証を走らせて終了コードを記録する。**
   - `uv run pytest tests`
   - `uv run ruff format --check --line-length 78 src tests`
   - `uv run ruff check --extend-select I src tests`
   - `uv run basedpyright src tests`
   - `uv run mypy src tests`
   落ちたら出力のまま引用する（要約しない）。

2. **CLI が動くか。** `uv run tmr --help`、`uv run tmr timer --help`、
   `uv run tmr pomodoro --help` が終了コード 0 で出ること。
   `pyproject.toml` の entry point を `tmr.cli:cli` に変えたので、
   **インストールされたスクリプト経由で動くことを必ず見る**。
   `uv run python -m tmr --help` も試す。

3. **指示のとおり全部やってあるか。** `instructions.md` の 1〜7 を 1 つずつ照合する。
   特に:
   - `src/tmr/__init__.py` が `__version__` だけになっているか
     （`logger` の再輸出、`SEC_MIN`/`MIN_HOUR`、`ESQ_*` が残っていないか）
   - `ESQ_EL0` / `ESQ_EL1` が `terminal.py` に**残っている**か（消していないか）
   - `BaseTimer` / `base_timer` / `tmr.utils` / `tmr.__main__ import` という
     文字列がソース・テスト・`CLAUDE.md`・`README.md` に残っていないか
     （`grep -rn` で確認。`archives/` は対象外）
   - `t_str()` が `timefmt.py` のモジュール関数になり、`timer.py` の
     `display()` 内にローカル定義が残っていないか

4. **挙動が変わっていないか。** この項目は移動と改名だけのはず。
   `git diff -M HEAD -- src/tmr/timer.py src/tmr/pomodoro.py` を見て、
   名前の付け替えと import 以外の変更（条件式、定数値、引数、順序）が
   入っていないか報告する。`t_str()` の切り出しは、中身が元と同じかを
   `git show HEAD:src/tmr/base_timer.py` と突き合わせて見る。

5. **`tests/test_timefmt.py` の中身。** 指示にある観点（分、`omit_sec`、
   時間単位、0 秒、59→60 秒の境界）を実際に見ているか。
   assert の期待値が実装をなぞっただけになっていないか（手で計算して確かめる）。

6. **`git status`** に残骸や、指示に無いファイルの変更が無いか。

## 報告

`archives/agents/TODO-009/verifier-report.md` に書く。
返事は 5 行以内（終わったか・報告ファイルのパス・判断が要る点）。
