# TODO-009 verifier 報告

`instructions.md` と `implementer-report.md` を読んだうえで確認した。

## 1. 検証コマンド（すべて終了コード 0）

```
$ uv run pytest tests -q
74 passed in 0.52s
EXIT:0

$ uv run ruff format --check --line-length 78 src tests
20 files already formatted
EXIT:0

$ uv run ruff check --extend-select I src tests
All checks passed!
EXIT:0

$ uv run basedpyright src tests
0 errors, 0 warnings, 0 notes
EXIT:0

$ uv run mypy src tests
Success: no issues found in 20 source files
EXIT:0
```

落ちたものは無い。

## 2. CLI 起動確認

- `uv run tmr --help` / `uv run tmr timer --help` /
  `uv run tmr pomodoro --help` / `uv run python -m tmr --help` は
  すべて終了コード 0。
- インストールされたスクリプト経由の確認: `uv run which tmr` で得た
  `.venv/bin/tmr` の中身を見たところ、
  ```
  from tmr.cli import cli
  ...
  sys.exit(cli())
  ```
  となっており、`pyproject.toml` の
  `[project.scripts] tmr = "tmr.cli:cli"` どおりに entry point
  スクリプトが再生成されていることを確認した。
- `uv run tmr timer 1` と
  `uv run tmr pomodoro -w 0.1 -b 0.1 -c 2` を実際に
  `< /dev/null`＋`timeout 5` で起動し、プログレスバー付きの表示
  （`Timer  1m ...` および `WORK:1/2 ...`）が出ることを確認した
  （`timeout` によるものなので終了コードは 124 だが、これは想定どおり）。

## 3. 指示の 1〜7 の照合

- `src/tmr/__init__.py`: `__version__` の定義と
  `__all__ = ["__version__"]` だけになっている。
  `logger` 再輸出、`SEC_MIN` / `MIN_HOUR`、`ESQ_*` は残っていない。
- `terminal.py`: `ESQ_EL0` / `ESQ_EL1` は使われていないが**残って
  いる**ことを確認した（指示どおり）。`ESQ_EL2` は `timer.py` から
  `from .terminal import ESQ_EL2` で参照している。
- `grep -rn` で `BaseTimer` / `base_timer` / `tmr.utils` /
  `tmr.__main__ import` を `src` / `tests` / `CLAUDE.md` /
  `README.md` に対して検索したところ、コード・テスト・`CLAUDE.md`・
  `README.md` には残っていない。**1 件だけ検出**:
  `src/tmr/mylog.py:80` の docstring に
  `` `__log = getLogger("BaseTimer")` `` という例示文字列が残っている。
  実装者はこれを「サンプルコード中の例示名であり、実在するクラスへの
  参照ではない」と判断して変更しなかった（implementer-report に明記
  あり）。指示文の対象は「参照元（`pomodoro.py`、テスト）」であり
  `mylog.py` は名指しされていないため、指示違反とは言えないが、
  **例として古いクラス名が残っている点は事実**なので報告する。
  直すかどうかは管理者の判断が要る。
- `t_str()`: `timefmt.py` にモジュール関数として定義されており、
  `timer.py` の `display()` からは `from .timefmt import t_str` を
  import して呼ぶだけになっている（`display()` 内のローカル定義は
  削除済み）。

## 4. 挙動の変化が無いか

`git diff --find-renames=30% HEAD -- src/tmr/timer.py
src/tmr/pomodoro.py src/tmr/base_timer.py` で確認。

- `pomodoro.py`: `from .base_timer import BaseTimer` →
  `from .timer import Timer` と、生成箇所・docstring の
  `BaseTimer` → `Timer` のみ。条件式・引数・順序の変更は無い。
- `base_timer.py` → `timer.py`（similarity index 96%）:
  - import を `from . import ESQ_EL2, MIN_HOUR, SEC_MIN` から
    `from .terminal import ESQ_EL2` / `from .timefmt import t_str` に
    変更
  - クラス名 `BaseTimer` → `Timer`、docstring `Base Timer.` →
    `Timer.`
  - `display()` 内のローカル関数 `t_str()` の削除（呼び出し側は
    そのまま `t_str(...)`）
  - それ以外の差分は無い（`similarity index 96%` の内訳はこれだけ）。
- `t_str()` の中身: `git show HEAD:src/tmr/base_timer.py` の旧ローカル
  定義（391〜406 行）と `timefmt.py` の新定義を突き合わせたところ、
  1 文字も変わらず同一（`divmod` の式、`omit_sec` の分岐、
  フォーマット文字列すべて一致）。

テストファイルについても、旧ファイルを `sed` で機械的に名前置換した
ものと新ファイルを diff したところ、以下の 2 点を除き完全一致した
（実質、行長超過による ruff format の折返し差のみ）:
- `tests/test_timer.py`: `with patch(...)` の折返しが 1 行にまとまった
  だけ（`tmr.timer.Terminal.cbreak` の行が短くなったため）
- 同ファイル: `def test_alarm_quit_by_quitcmd(...)` の引数リストの
  折返しが 1 行にまとまっただけ

`tests/test_cli.py`（旧 `test_timer.py`）、`tests/test_terminal.py`
（旧 `test_utils.py`）、`tests/test_integration_alarm.py`、
`tests/test_config.py`、`tests/test_pomodoro.py` はいずれも
import／`patch()` 文字列の付け替えのみで、アサーションやロジックの
変更は無い。

## 5. `tests/test_timefmt.py` の中身

7 件のテストがあり、以下の観点をすべて確認している:
分単位（秒あり／`omit_sec` で秒省略／`omit_sec` でも秒が残る場合は
省略しない）、時間単位（秒あり／`omit_sec`）、0 秒、境界
（59 秒→60 秒の繰り上がり）。

期待値を実装をなぞらず手計算で検算した（`divmod` を手で追った）:

- `t_str(65)` → `divmod(65,60)=(1,5)` → `" 1m05s"` … 一致
- `t_str(60, omit_sec=True)` → `divmod(60,60)=(1,0)`、`s==0` →
  `" 1m"` … 一致
- `t_str(65, omit_sec=True)` → `s=5≠0` のため通常の書式 →
  `" 1m05s"` … 一致
- `t_str(3661)` → `divmod(3661,60)=(61,1)` → `h,m=divmod(61,60)=(1,1)`
  → `"1h01m01s"` … 一致
- `t_str(3660, omit_sec=True)` → `h,m=(1,1)`、`s=0` → `"1h01m"` … 一致
- `t_str(0)` → `" 0m00s"` … 一致
- `t_str(59)` → `" 0m59s"`、`t_str(60)` → `" 1m00s"`（60 秒で
  1 分へ繰り上がる境界）… 一致

期待値の書き写し・実装なぞりは見られなかった。

## 6. `git status`

```
Changes to be committed:
  renamed:    src/tmr/utils.py -> src/tmr/terminal.py
  renamed:    src/tmr/base_timer.py -> src/tmr/timer.py
  deleted:    tests/test_base_timer.py
  new file:   tests/test_cli.py
  renamed:    tests/test_utils.py -> tests/test_terminal.py
  modified:   tests/test_timer.py

Changes not staged for commit:
  modified:   CLAUDE.md
  modified:   pyproject.toml
  modified:   src/tmr/__init__.py
  modified:   src/tmr/__main__.py
  modified:   src/tmr/pomodoro.py
  modified:   src/tmr/terminal.py
  modified:   src/tmr/timer.py
  modified:   tests/test_cli.py
  modified:   tests/test_config.py
  modified:   tests/test_integration_alarm.py
  modified:   tests/test_pomodoro.py
  modified:   tests/test_terminal.py
  modified:   tests/test_timer.py

Untracked files:
  archives/agents/TODO-009/
  src/tmr/cli.py
  src/tmr/timefmt.py
  tests/test_timefmt.py
```

指示の範囲外のファイルの変更は無い。すべて指示 1〜7 の対象ファイルと
一致している。残骸（`base_timer.py` / `utils.py` / 旧
`test_base_timer.py` / `test_utils.py` などの unstaged 残り）も無い。

`git diff HEAD -- pyproject.toml src/tmr/__init__.py` も確認し、
`[project.scripts]` の書き換えと `__init__.py` の削減内容が
指示どおりであることを確認した。`README.md` は差分無し（実装者の
報告どおり、元々 `base_timer` / `utils.py` などへの言及が無かった）。

## 判断が要る点・確かめられなかったこと

1. **`src/tmr/mylog.py:80` の docstring 例 `getLogger("BaseTimer")`。**
   実在コードへの参照ではなく例示文字列だが、クラス名が古いままなので
   直すかどうかは管理者の判断が要る（実装者も同じ懸念を報告済み）。
2. **`docs/mylog.md` に `BaseTimer` / `__main__.py` の CLI コマンド /
   `TMR_LOG=BaseTimer=DEBUG` の記述が残っている。** ただし
   `TMR_LOG` は TODO-003 で既に廃止済みであり、この文書は
   TODO-009 着手前から古くなっていたと見られる。TODO-009 の指示
   （7. 文書）は `CLAUDE.md` と `README.md` だけを対象にしており
   `docs/mylog.md` は名指しされていないため、今回の実装漏れとまでは
   判断できない。存在自体は事実として報告する（直すかどうか、
   別項目にするかは管理者判断）。
3. `TODO.md` の TODO-009 の節に旧名（`base_timer.py` / `BaseTimer` /
   `utils.py`）が残っているが、これは項目の計画文なので変更対象では
   ないと判断した（決着時に archives へ移す際の扱いは管理者次第）。

以上を除き、指示との食い違いや挙動の変化は見つからなかった。
