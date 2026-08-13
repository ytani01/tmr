## TODO-005. `mylog.setLevel()` で変えた水準を既定に戻す API を足す

### きっかけ

`setLevel(name, level)` は名前ごとの水準を `_levels` という内部の
辞書に書き込むだけで、明示的に既定へ戻す公開 API が無かった。
`_levels` はモジュール内部の変数（アンダースコア始まり）なので、
外から `del` するのは行儀が悪い。`loggerInit()` を呼び直しても、
個別に `setLevel()` した名前のエントリは残るため既定に戻せなかった。

### やったこと

- `mylog.py` の `setLevel(name, level)` の `level` を
  `str | None = None` にし、省略時（`None`）は `_levels` から該当
  エントリを消して既定水準にフォールバックするようにした
  （最初は `resetLevel(name)` という専用関数を独断で作ったが、
  「余計な関数を増やしたくない、`setLevel(level=None)` のほうが
  いい」とレビューで指摘され、この形に直した）
- `name == ""`（既定水準そのもの）に対して `level=None` を渡した
  場合は、`_levels[""]` を消すと他の名前のフォールバック先が
  無くなって壊れるため、何もしない（no-op）ようにした
- `tests/test_mylog.py` にテストを追加
  （既定に戻ることの確認と、未設定の名前に対する no-op の確認）
- `CLAUDE.md` の「ログ」節に `setLevel(name, None)` の一文を追記

### テスト

`uv run pytest tests`（55 件）、`ruff format` / `ruff check`（対象
ファイルにはエラー無し。`base_timer.py` 等の既存の指摘は今回の
変更と無関係なので手を付けていない）、`basedpyright` / `mypy` を
`mylog.py` / `test_mylog.py` に対して実行し、すべて通過を確認した。
