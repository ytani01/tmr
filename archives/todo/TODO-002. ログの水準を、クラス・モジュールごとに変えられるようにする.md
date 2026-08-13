## TODO-002. ログの水準を、クラス・モジュールごとに変えられるようにする

### きっかけ

`loggerInit(debug)` が全体を DEBUG か INFO のどちらかにするだけで、
各モジュールは loguru のグローバル `logger` を直接呼んでいたため、
`BaseTimer` のデバッグ出力だけを見る、といったことができなかった。

### やったこと

- `mylog.py` に `getLogger(name)` を追加。`logger.bind(log_name=name)`
  を返す。呼ばれた名前は `_registered_names` に記録する
- sink の `filter` で名前ごとの水準を判定する `_make_filter()` を実装。
  `record["extra"]["log_name"]` が無ければモジュール名にフォールバック
  するので、素の `logger.debug()` が残っていても壊れない
- 環境変数 `TMR_LOG`（例: `BaseTimer=DEBUG,main=INFO`）を
  `_parse_tmr_log()` で解釈し、`loggerInit()` に反映
- `TMR_LOG` に、どの `_log` にも使われていない名前が書かれていたら
  warning を出す（`_registered_names` にない名前を検出）
- `base_timer.py`（`_log = getLogger("BaseTimer")`、約20か所）、
  `progress_bar.py`（`_log = getLogger("ProgressBar")`、1か所）、
  `__main__.py`（`_log = getLogger("main")`、5か所）を
  `logger.` → `_log.` に置換
- `CLAUDE.md` の「ログ」の節を、`_log` 経由の呼び出しと `TMR_LOG` の
  説明に更新

### 決めたこと

- 知らない名前が書かれていたら **warning を出す**（黙って無視しない）
- `LOG_FMT` は**今のまま**（`{file}:{line}` のみ。`log_name` は
  フォーマットに出さない）
- CLI オプション（`--log-level`）は**足さない**。`TMR_LOG` のみ

### テスト

`tests/test_mylog.py` に追加（9件）:

- `_parse_tmr_log()` の単体テスト（正常系・空文字列・不正な項目）
- 既定水準（`debug=False` で INFO、`debug=True` で DEBUG）
- `log_name` を持たない素の `logger` 呼び出しがモジュール名で出ること
- `TMR_LOG` で名前ごとに水準が変わること
- `TMR_LOG` に知らない名前があると warning が出ること／
  知っている名前では出ないこと

`uv run pytest tests`、`ruff format` / `ruff check` / `basedpyright` /
`mypy` はすべて通過を確認。
