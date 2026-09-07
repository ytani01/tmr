# TODO-011. `docs/mylog.md` を消し、`mylog.py` の docstring に寄せる

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort high | verifier |
| 実施 | Opus 5 / effort medium | verifier |

| 担当 | モデル | effort | output | cache_creation | 料金の割合 |
|------|--------|--------|--------|----------------|-----------|
| main | Opus 5 | medium | 6,507 | 40,655 | 85% |
| verifier | Sonnet 5 | 記載なし | 2,866 | 32,982 | 15% |
| 合計 |  |  | 9,373 | 73,637 | 概算 $1.0 |

- verifier は定義のモデルが haiku。旧ファイルの記述を 1 つずつ現行コードと
  突き合わせる判断が要るので Sonnet 5 に上書きした
- verifier の定義には `effort` の行が無い

## きっかけ

`docs/mylog.md` は TODO-002 のときに書いたもので、その後の TODO-003
（`TMR_LOG` の廃止）・TODO-004（`__qualname__`）・TODO-005
（`setLevel(name, None)`）・TODO-009（`__main__.py` → `cli.py`、
`BaseTimer` → `Timer`）が反映されていなかった。書き直すと元の形がほとんど
残らない量で、しかもどこからもリンクされていない（`README.md` が参照して
いるのは `docs/fig1.png` だけ）。

古くなった原因は、同じ話が `docs/mylog.md`・`mylog.py` の冒頭 docstring・
`CLAUDE.md` の「ログ」節の 3 箇所にあったこと。**消して 2 箇所に減らす**
と決めた（2026-09-08）。

古かった記述:

| 記述 | 現状 |
|---|---|
| `TMR_LOG` の節まるごと | 廃止（TODO-003） |
| `_registered_names` に登録される | そんな変数は無い（`_levels` だけ） |
| 未使用の名前を書くと warning が出る | 無い |
| 名前無しはモジュール名にフォールバックする | しない（既定水準を使うだけ） |
| モジュール先頭の `_log = getLogger("MyModule")` が基本 | クラス本体の `__log = getLogger(__qualname__)`（TODO-004） |
| `__main__.py` の CLI コマンド例、`BaseTimer` | `cli.py`、`Timer`（TODO-009） |

## やったこと

- `src/tmr/mylog.py` の冒頭 docstring に、`getLogger` と `loggerInit` の
  役割の違いの表を移した。`TMR_LOG` の行は削り、「呼ぶ場所」も
  クラス本体（`__qualname__`）に合わせて書き直した。表のあとに、
  名前ごとの水準が `loggerInit()` で上書きされないことを添えた
- `docs/mylog.md` を `git rm` した
- `docs/` に残るのは `fig1.png` だけになったが、`README.md` が
  `docs/fig1.png` を参照していて存在理由が読み取れるので、
  `CLAUDE.md` にも `README.md` にも記述を足さなかった

## 確かめたこと

- `uv run pytest tests -q` → 74 passed
- `uv run ruff format --line-length 78 src tests` → 差分なし
- `uv run ruff check --extend-select I src tests` → All checks passed!
- `uv run basedpyright src tests` → 0 errors
- `uv run mypy src tests` → Success

verifier に、消した記述のうち現在も有効なものが残っているか、docstring が
現行の実装と矛盾しないかを照合させた（報告は
`archives/agents/TODO-011/verifier-report.md`）。挙がった判断点は 2 つとも
対応しないことにした。

- **`docs/` に `fig1.png` だけ残る旨の記述** — `README.md` から参照されて
  いるので不要
- **「名前が重複するとき」（1 モジュールに 2 クラスあるときは
  `_log_foo` / `_log_bar` と分ける）** — クラス本体の
  `__qualname__` で名前が決まる今の書き方（TODO-004）では起きない話なので、
  意図して落とした

## 分担の振り返り

- verifier は、依頼に無かった「消した情報のうち残すべきものが無いか」を
  1 項目ずつ突き合わせ、判断が要る点として 2 つ挙げてきた。どちらも
  結論は「対応しない」だったが、落としたのが意図なのか見落としなのかを
  main 自身では区別できない類いの指摘で、分けた効果が出た
- 見込みは Opus 5 / effort high だったが、決まっていることを写す作業が
  ほとんどで medium で足りた。担当の見込み（verifier のみ）は合っていた
- 同じ規模——文書と docstring だけで、書き換えの根拠が現行コードにある
  項目——なら、次も main が書いて verifier に照合させる形でよい。
  依頼をファイルにせずプロンプトへ直接書いたのも、確認項目が 5 つで
  収まる規模なら妥当だった
