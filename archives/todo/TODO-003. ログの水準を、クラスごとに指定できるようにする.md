## TODO-003. ログの水準を、クラスごとに指定できるようにする

### きっかけ

名前ごとの水準は環境変数 `TMR_LOG`（[[TODO-002]]）からしか
指定できなかった。実行時に環境変数で切り替える用途は無く、コードを
編集すれば足りる。一方、同じファイルにある複数のクラスや、親子
（継承）を別々の水準にしたい。これが必須だった。

### やったこと

- `mylog.py` を書き直した。`_levels: dict[str, int]` で名前ごとの
  水準を数値で持ち、`setLevel(name, level)` で設定する。
  `getLogger(name, level=None)` は `level` を渡すと `setLevel()` を
  呼ぶだけ。`loggerInit()` は `_levels[""]`（既定水準）だけを
  入れ直すので、`getLogger()` で指定した名前ごとの水準は
  `loggerInit()` を呼ぶ順に関わらず残る
- `TMR_LOG` / `_parse_tmr_log()` / `_registered_names` /
  `_make_filter()` / 知らない名前の warning を削除
  （113 行 → 96 行）
- `base_timer.py`（`BaseTimer`）と `progress_bar.py`
  （`ProgressBar`）の `_log = getLogger(...)`（モジュール先頭）を、
  クラス本体の `__log = getLogger(...)`（アンダースコア 2 つ）に
  移した。呼び出し側は `_log.debug(...)` → `self.__log.debug(...)`
  に置換。名前修飾で `self._BaseTimer__log` に解決されるため、
  子クラスのインスタンスから親のメソッドを呼んでも親の名前で出る
- `__main__.py`（クラスの無いモジュール）は、従来どおり
  モジュール先頭の `_log = getLogger("main")` のまま
- `CLAUDE.md` の「ログ」節を、クラス本体の `__log` と
  `getLogger(name, level)` / `setLevel(name, level)` の説明に更新
- `archives/todo/TODO-002. ….md` に、`TMR_LOG` を本項目で
  廃止した旨を追記

### テスト

`tests/test_mylog.py` を新しい API に合わせて書き直した（6件）:

- 既定水準（`debug=False` で INFO、`debug=True` で DEBUG）
- `log_name` を持たない素の `logger` 呼び出しが既定水準に従うこと
- `getLogger(name, level)` で名前ごとに水準が変わること
- `getLogger(name, level)` の指定が、後から呼んだ `loggerInit()` でも
  消えないこと
- `setLevel(name, level)` で既定より高い水準に絞れること

`uv run pytest tests`、`ruff format` / `ruff check` / `basedpyright` /
`mypy` はすべて通過を確認。
