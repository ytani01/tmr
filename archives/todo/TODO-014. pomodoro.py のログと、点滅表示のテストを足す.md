# TODO-014. `pomodoro.py` のログと、点滅表示のテストを足す

|      | main | 担当 |
|------|------|------|
| 見込み | Sonnet 5 / effort medium | implementer + verifier |
| 実施 | Opus 5 / effort high | implementer + verifier |

| 担当 | モデル | effort | output | cache_creation | 料金の割合 |
|------|--------|--------|--------|----------------|-----------|
| main | Opus 5 | high | 7,934 | 54,782 | 73% |
| implementer | Sonnet 5 | medium | 1,439 | 41,795 | 13% |
| verifier | Sonnet 5 | 記載なし | 583 | 38,492 | 13% |
| 合計 |  |  | 9,956 | 135,069 | 概算 $1.6 |

- verifier は定義のモデルが haiku。点滅の分岐をわざと壊して落ちることを
  確かめる手順があり、テストの読み方に判断が要るので Sonnet 5 に上書きした
- verifier の定義には `effort` の行が無い（haiku 前提で書かれているため）
- main は利用者が Opus 5 のまま着手した（見込みは Sonnet 5 だった）

## きっかけ

TODO-010 で `Timer` を分割したときのレビューで挙がった残件。

- `PomodoroTimer` だけ、クラス本体の `__log = getLogger(__qualname__)` が
  無く、`CLAUDE.md` のログ規約から漏れていた。TODO-010 で足した
  `phases()` はクラスの外にあるので、モジュール先頭の `_log` も要る
- `TimerView.display()` の点滅（`pause_blink` の列と、満了時の `state`）は
  `CLAUDE.md` に書いてある仕様なのに、直接のテストが無かった

どちらも挙動は変えない。

## やったこと

### `src/tmr/pomodoro.py`

- モジュール先頭に `_log = getLogger("pomodoro")` を置き、`phases()` の
  先頭で `_log.debug(f"config={config}")`
- `PomodoroTimer` のクラス本体に `__log = getLogger(__qualname__)` を置き、
  `__init__` / `run()` / `_run_timer()` で `self.__log.debug(...)`
- 書き方（引数を出す、引数の無いところは `debug("")`）は `clock.py` に
  揃えた。`PomodoroConfig.__post_init__` の検証にはログを足していない
  （例外で十分）

### `tests/test_view.py`

点滅を見るテストを 2 件足した。

- `test_display_pause_blink` — ポーズの有無で、`pause_blink=True` の列
  （`rate`）に渡る `blink` が `False → True` に変わること
- `test_display_timeup_blink` — 満了時に `state` 列が `blink=True` で
  出ること

`display()` は `click.secho()` ではなく `click.style()` で色と点滅を
付けているので、テストの対象は `click.style` の呼び出し。

呼び出しを「表示文字列をキーにした辞書」にすると、別の列が同じ文字列に
なったとき取り違える。verifier の指摘を受けて `blink_map()` という補助を
作り、その中で**キーの数と呼び出し回数が一致すること**を確かめるように
した。将来値が衝突したら、そこで落ちる。

## 確かめたこと

- `uv run pytest tests` → 150 passed
- `uv run ruff format --line-length 78 src tests` / `ruff check` /
  `basedpyright` / `mypy` すべて通過
- **点滅の分岐をわざと壊して、足したテストが落ちることを確かめた**
  （verifier が実施）。`if col.pause_blink and clock.is_paused:` を潰すと
  `test_display_pause_blink` だけが落ち、
  `if col.name == "state" and clock.is_timeup:` を潰すと
  `test_display_timeup_blink` だけが落ちる。どちらも狙った分岐だけを
  見ている
- 既存の `test_display_pause_state` / `test_display_timeup_state` は
  `col["state"].value` の文字列を見るテストで、役割が重なっていないことも
  確かめた

## 分担の振り返り

- **implementer** は依頼どおり実装した。依頼書に `click.secho` と書いて
  あったのが誤り（実装は `click.style`）で、そこを黙って合わせるのでは
  なく、報告に理由を書いて挙げてきた
- **verifier** は「分岐をわざと壊して落ちるか」を実際にやり、2 件とも
  狙った分岐だけを見ていることを示した。そのうえで、テストが値の文字列を
  キーにしている脆さを挙げた。これは pytest を通すだけでは出てこない
  指摘で、確認を分けた効果がそのまま出た
- 見込みとの食い違いは main のモデルだけ（Sonnet 5 の見込みで Opus 5 の
  まま着手した）。担当の編成は見込みどおり
- **次に同じ規模（1 ファイルのログ追加 + テスト 2 件）をやるなら、同じ
  編成でよい。** ただし main が $1.2 で 73% を占めており、ここが重い。
  依頼書を 2 通書いてから起動する形は変えなくてよいが、実装と確認の
  依頼書は着手時にまとめて 1 度に書けば、main の往復が 1 回減る
- verifier のモデルを haiku から Sonnet 5 に上げた判断は残す。「わざと
  壊して落ちるか確かめる」は手順が決まっているように見えて、どの行を
  どう壊すかの判断が要る
