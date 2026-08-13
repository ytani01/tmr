## TODO-001. 設定ファイル（`~/.config/tmr/config.toml`）から既定値を読む

### きっかけ

時間・タイトル・色などをすべてコマンドライン引数で毎回渡していた。
よく使う値を設定ファイルに書いておけるようにしたかった。

### 決めたこと

着手時に利用者へ確認して決めた。

- **対象にする項目。** `timer` / `pomodoro` の全オプション。
  `timer` の `minutes` は引数だが、これも対象にした
  （もともと TODO 本文が「それぞれの時間」を候補に挙げていたため。
  これを外すと `timer` で一番使う値が設定できなくなる）
- **優先順位。** コマンドライン引数 > 設定ファイル > コードの既定値
- **ファイルが無いとき。** 黙ってコードの既定値を使う。
  当初「無いときもエラーで終了」と回答されたが、それだと設定ファイルを
  作るまで `tmr` が一切起動しなくなる旨を伝えて確認し直し、この形にした
- **壊れているとき。** エラーで終了する。TOML の構文エラーのほか、
  **知らないセクション・知らないキー**もエラーにする（書き間違いに
  その場で気づけるように）
- **置き場所。** `~/.config/tmr/config.toml`（XDG 準拠）

### やったこと

- `src/tmr/config.py` を新設した
  - `config_path()` — `XDG_CONFIG_HOME` があればその下、無ければ
    `~/.config` の下の `tmr/config.toml`
  - `load_config(group)` — TOML を読み、`click` の `default_map` を作る。
    セクション名はサブコマンドの**正式名**のみ許し、別名（`t` / `p`）にも
    同じ dict を張るので `tmr t` でも `[timer]` が効く。キーは
    オプション名から `--` を取ったもので、`-` と `_` のどちらでも書ける
  - `ConfigGroup` — `click.Group` の子。`make_context()` の中で設定を
    読んで `default_map` に入れる
- `__main__.py` の `cli` を `@click.group(cls=ConfigGroup)` にし、
  読んだ結果を `ctx.default_map` としてデバッグ出力するようにした
- 優先順位は `click` の `Context.default_map` がそのまま面倒を見るので、
  **各コマンドの定義（`@click.option(...)`）には手を入れていない**
- `config.py` ではログを出さない。`loggerInit()` より前に動くため、
  `loguru` の既定ハンドラに素通しされて毎回出てしまうから
- `tests/test_config.py`（13 件）を追加
- `README.md` に「設定ファイル」の節を足した。あわせて、`CLAUDE.md` が
  「古い」と書いていた `timer` の help 出力（`--title` /
  `--title-color` が載っていなかった）を実際の出力に直した
- `CLAUDE.md` の「設計」に「設定ファイル」の節を足した

### テスト

`uv run pytest tests` — 68 件すべて通過（うち `test_config.py` が
13 件）。既存のテストは `timer` / `pomodoro` を**直接** `invoke()` して
いるため設定ファイルを読まず、影響を受けない。設定を絡めたテストは
`cli` から呼び、`XDG_CONFIG_HOME` を `tmp_path` に向けている。

`ruff format` / `ruff check --extend-select I` / `basedpyright` / `mypy`
を実行。`basedpyright` は 0 件。`ruff` の 8 件と `mypy` の 2 件は
`base_timer.py` / `progress_bar.py` / `test_base_timer.py` の既存の
指摘で、変更前（`git stash` 状態）と同数であることを確認した。

手元で `XDG_CONFIG_HOME` を差し替えて、実際の CLI でも確認した。
設定からの既定値、コマンドライン引数による上書き、別名 `t`、TOML の
構文エラー、知らないセクション、知らないキー、型違い、ファイル無しの
それぞれが期待通りに動いた。
