# TODO-009. モジュール構成を整理する（移動と改名だけ）

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort high | implementer + verifier |
| 実施 | Opus 5 / effort high | implementer + verifier |

| 担当 | モデル | effort | output | cache_creation | 料金の割合 |
|------|--------|--------|--------|----------------|-----------|
| main | Opus 5 | high | 12,513 | 62,670 | 45% |
| implementer | Sonnet 5 | medium | 5,819 | 101,353 | 38% |
| verifier | Sonnet 5 | 記載なし | 8,175 | 71,957 | 17% |
| 合計 |  |  | 26,507 | 235,980 | 概算 $3.1 |

- implementer は定義のモデルが sonnet。移動と改名だけで判断が要らないので
  そのまま使った
- verifier は定義のモデルが haiku。照合する項目が多く、旧ファイルとの
  diff の突き合わせまで頼んだので Sonnet 5 に上書きした
- verifier の定義には `effort` の行が無い（元が Haiku 向けの定義のため）

## きっかけ

`base_timer.py` が 533 行あり、名前・置き場所・役割がずれていた。

- `BaseTimer` という名前だが、継承される基底クラスではない。
  `PomodoroTimer` は継承せず、順番に呼び出すだけ
- `__init__.py` にパッケージの入口と関係ない定数
  （`SEC_MIN` / `MIN_HOUR` / `ESQ_*`）が置いてあった
- `utils.py` の中身は端末の後始末だけで、名前が中身を表していない
- `__main__.py` に click のコマンド定義が全部入っていた
- 時刻の整形 `t_str()` が `display()` の中のローカル関数で、単体テストが
  書けなかった

分割そのもの（TODO-010）に入る前に、移動と改名だけを先に済ませて
差分を読めるようにした。

## やったこと

挙動は変えていない。

- `base_timer.py` → `timer.py`、`BaseTimer` → `Timer`
- `utils.py` → `terminal.py`。`__init__.py` にあった `ESC` / `ESQ_*` も移した
- `timefmt.py` を新設。`SEC_MIN` / `MIN_HOUR` と、`display()` 内のローカル関数
  だった `t_str()` をモジュール関数に出した
- `__init__.py` は `__version__` だけにした（`loguru` の `logger` の
  再輸出も消した。どこからも使っていなかった）
- `cli.py` を新設して click のコマンド定義を移した。`__main__.py` は
  `python -m tmr` の入口だけになり、`pyproject.toml` の
  `[project.scripts]` は `tmr = "tmr.cli:cli"` を指すようにした
- テストの改名: `test_timer.py`（CLI のテスト）→ `test_cli.py`、
  `test_base_timer.py` → `test_timer.py`、`test_utils.py` → `test_terminal.py`。
  `test_timefmt.py` を新設し、`t_str()` の単体テストを 7 件書いた
- `CLAUDE.md` の記述を新しい名前に直した。`mylog.py` の docstring に
  例として残っていた `getLogger("BaseTimer")` は `getLogger(__qualname__)`
  にした（モジュール冒頭のサンプルと揃えた）

`ProgressBar.display()` と `ESQ_EL0` / `ESQ_EL1` は本体から使っていないが、
ライブラリとして使う側のために残した（2026-09-08 に決めた）。

`README.md` はモジュール名に触れていなかったので変更なし。

## 確かめたこと

- `uv run pytest tests` … 74 passed
- `uv run ruff format --check --line-length 78 src tests` … 20 files already formatted
- `uv run ruff check --extend-select I src tests` … All checks passed
- `uv run basedpyright src tests` … 0 errors
- `uv run mypy src tests` … Success: no issues found in 20 source files
- `uv run tmr --help` / `tmr timer --help` / `tmr pomodoro --help` /
  `python -m tmr --help` が終了コード 0。`.venv/bin/tmr` の中身が
  `from tmr.cli import cli` に変わっていることも見た
- `uv run tmr timer 1` と `uv run tmr pomodoro -w 0.1 -b 0.1 -c 2` を
  実際に起動し、表示が出ることを確認
- `git diff -M` で、`timer.py` / `pomodoro.py` の差分が名前の付け替えと
  import だけであることを照合。`t_str()` は旧ローカル定義と 1 文字も
  違わないことを `git show HEAD:src/tmr/base_timer.py` と突き合わせて確認
- テストは旧ファイルを機械的に名前置換したものと diff し、差が
  ruff format による折返しの 2 箇所だけであることを確認
- `test_timefmt.py` の期待値は `divmod` を手で追って検算

詳しくは `archives/agents/TODO-009/verifier-report.md`。

## 分担の振り返り

- **implementer が見つけたもの**: テストのファイル名の衝突
  （`test_base_timer.py` → `test_timer.py` が既存の `test_timer.py` と
  ぶつかる）は依頼の時点で管理者が潰していたので、実装は素直に進んだ。
  implementer 自身が報告してきたのは `mylog.py` の docstring に残った
  `BaseTimer` の 1 件
- **verifier が見つけたもの**: `mylog.py` の 1 件（implementer と同じ）に
  加えて、`docs/mylog.md` に廃止済みの `TMR_LOG` と `__main__.py` の記述が
  残っていること。これは TODO-003 の時点から古かったもので、今回の
  漏れではない。旧ファイルとの diff の突き合わせと `t_str()` の
  期待値の検算まで自分でやって、挙動が変わっていないことを裏付けた
- **見込みとの食い違い**: 担当の構成は見込みどおり。モデルだけ、verifier を
  定義の Haiku から Sonnet 5 に上げた。照合する項目が 6 つあり、
  「旧ファイルとの機械置換 diff」のような手順を自分で組み立てる必要が
  あったため。結果として、指示に無かった `docs/mylog.md` の指摘まで拾えた
- **次に同じ規模なら**: 依頼文（`instructions.md`）に手順を書き切ったぶん
  implementer は安く済んだ（$1.2、判断待ちゼロ）。この形は保つ。
  減らせるのは main の分で、実装前に自分でソースを読んで回った $1.4 のうち
  半分は、`Explore` に「どのファイルがどの定数を参照しているか」を
  出させれば済んだ。ただし今回は依頼文の精度がそのまま implementer の
  安さになったので、下調べを削るのは慎重に

## 残ること

- `docs/mylog.md` が古い（TODO-003 で廃止した `TMR_LOG` の記述、
  `__main__.py` に CLI コマンドがある前提の記述）。TODO-009 の範囲外
- 分割そのものは TODO-010
