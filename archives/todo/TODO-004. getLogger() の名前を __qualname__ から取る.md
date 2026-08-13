## TODO-004. `getLogger()` の名前を `__qualname__` から取る

### きっかけ

`getLogger("BaseTimer")` のようにクラス名を文字列で手書きしていたが、
クラス本体では `__qualname__` が暗黙に設定されているので、
クラス名を手で書かなくても `getLogger(__qualname__)` で同じ名前が
取れる。クラス名を変えたときに `getLogger()` の引数を書き換え忘れる
心配が無くなる。

### やったこと

- `base_timer.py`（`BaseTimer`）と `progress_bar.py`（`ProgressBar`）
  の `__log = getLogger("BaseTimer")` などを
  `__log = getLogger(__qualname__)` に変更
- `mylog.py` の docstring の sample（`Base` / `Child` の例）を
  `getLogger(__qualname__)` を使う形に直した
- `CLAUDE.md` の「ログ」節に、`__qualname__` を使う理由を追記

### テスト

`uv run pytest tests`、`ruff format` / `ruff check` / `basedpyright` /
`mypy` はすべて通過を確認。加えて `loggerInit()` 後に
`BaseTimer._BaseTimer__log.debug(...)` /
`ProgressBar._ProgressBar__log.debug(...)` を呼び、フィルターを
通って出力されることを手元で確認した（名前が正しく `"BaseTimer"` /
`"ProgressBar"` になっている）。
