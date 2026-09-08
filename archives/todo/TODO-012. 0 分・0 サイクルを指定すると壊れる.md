# TODO-012. 0 分・0 サイクルを指定すると壊れる

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort medium | implementer + reviewer + verifier |
| 実施 | Opus 5 / effort high | implementer + reviewer + verifier |

| 担当 | モデル | effort | output | cache_creation | 料金の割合 |
|------|--------|--------|--------|----------------|-----------|
| main | Opus 5 | high | 42,977 | 187,425 | 37% |
| reviewer | Opus 5 | high | 24,676 | 399,456 | 36% |
| implementer | Sonnet 5 | medium | 13,797 | 367,480 | 24% |
| verifier | Haiku 4.5 | 記載なし | 10,511 | 166,101 | 3% |
| 合計 |  |  | 91,961 | 1,120,462 | 概算 $14.3 |

- reviewer は定義のモデルが sonnet。挙動と分岐が変わる項目なので
  Opus 5 に上書きした（`~/.claude/CLAUDE.md` の「挙動が変わる項目、
  分岐や条件式が変わる項目には、確認の担当とは別にレビューの担当も入れる」）
- implementer は定義のまま（sonnet / medium）。範囲が明確で、
  設計は main が決めたので上書きしなかった
- verifier は定義に `effort` の行が無い（Haiku は effort に対応しない）
- 立てたのは TODO-010 のコミットと同じ回（`a40cc83`）で、着手まで
  空いたため、集計は `--since '2026-09-08 03:55:00'` で切った

## きっかけ

TODO-010 の reviewer が、分割後のコードを読んでいて気づいた。
分割で持ち込んだものではなく、それ以前からある。

着手してまず再現した。**コードを読んだだけの見立てより広かった。**

| 指定 | 現象 |
|---|---|
| `tmr timer 0` | `TimerClock.rate` が `elapsed / t_limit` でゼロ除算。トレースバックで異常終了 |
| `tmr timer -- -1` | 即満了扱いになり、アラームが鳴り続けて止まらない |
| `tmr pomodoro -c 0` / `-c -1` | `phases()` が何も yield しないまま `while True` を回り続けて固まる |
| `tmr pomodoro -w 0` | `timer 0` と同じゼロ除算 |

負値は TODO.md の節に書いていなかった分。`Timer.main()` は満了判定より
前に `_display()` を呼ぶので、`rate` には必ず到達する。

## 決めたこと

**0 以下は受け付けない**（「0 として動かす」ことはしない）。
弾く場所は CLI とライブラリ層の両方にする。`Timer` / `PomodoroTimer` を
ライブラリとして直接使う経路は CLI を通らないため。

境界は用途で分けた。

| 対象 | 境界 | 理由 |
|---|---|---|
| `timer` の分数、`-w` / `-b` / `-l` | 0 より大きい | 0 分のタイマーに意味が無い |
| `-c`（サイクル数） | 1 以上 | 0 サイクルに意味が無い |
| `--alarm-count` | 0 以上 | 0 は「鳴らさない」 |
| `--alarm-sec1` / `--alarm-sec2` | 0 以上 86400 以下 | 0 は「間を空けない」。上限は下記 |

## やったこと

### CLI で弾く

`src/tmr/cli.py` の型を `click.IntRange` / `click.FloatRange` にした。
`nan` / `inf` は `FloatRange` を素通りするので、後段のコールバック
`_reject_non_finite()` で `click.BadParameter` にする。3 つの
オプションで同じ処理なので 1 つにまとめた。

設定ファイル（`~/.config/tmr/config.toml`）由来の値にも効く。
TOML は `nan` / `inf` を float リテラルとして持つので、これは必要だった。

### ライブラリ層でも弾く

- `TimerClock.__init__` — `not math.isfinite(t_limit) or t_limit <= 0`
- `PomodoroConfig.__post_init__` — 4 フィールドすべて
- `AlarmParams.__post_init__` — `count >= 0`、`sec1` / `sec2` は
  有限かつ `0` 以上 `SEC_DAY` 以下

`PomodoroConfig` は `@dataclass(frozen=True)` にした。検証を
`__post_init__` に集めた以上、構築後に `config.cycles = 0` と代入されると
すり抜けるため。`AlarmParams` には元から frozen の前例があった。

### レビューで見つかり、一緒に塞いだ穴

再現していた 0 と負値のほかに、同じ種類の穴が 3 つ出た。

- **`nan` / `inf`** — `is_timeup` の `elapsed >= nan` が常に False に
  なり、タイマーが永久に満了しない
- **アラームの 3 オプション** — `time.sleep(-1.0)` / `time.sleep(nan)` が
  `ValueError` を投げると、`thr_alarm()` の daemon スレッドが末尾の
  `alarm_active = False` に到達せずに死ぬ。`Timer.main()` の
  `while self.alarm_active` が抜けられなくなる
- **アラーム間隔の巨大な値** — `time.sleep(1e18)` は
  `OverflowError: timestamp out of range for platform time_t` になり、
  上と同じくスレッドが死ぬ。上限を 1 日（`timefmt.SEC_DAY`）にした

タイマー本体（分数、`-w` / `-b` / `-l`）に上限は足していない。
`time.sleep()` に渡らないので `OverflowError` にならず、長いタイマーは
指定として意味が通るため。

### 文書

- `CLAUDE.md` の設計の節に、二重に弾く作りと、**アラームだけ 0 を許す**
  ことを書いた。次に触る人が境界を「揃えて」しまわないようにするため
- `README.md` の `timer --help` / `pomodoro --help` を実出力に合わせた
  （`INTEGER RANGE` / `FLOAT RANGE` と範囲表示が付く）

## 確かめたこと

- 再現していた 4 つの現象が、すべて usage error（終了コード 2）になり、
  固まらず、トレースバックも出ないこと（pty 上で実行）
- 追加した `nan` / `inf` / 負値 / 上限超えも同じく usage error になること
- **正常系が壊れていないこと** — `-w 0.1` のような小さい正の小数、
  `--alarm-count 0`、`--alarm-sec1 0`、上限ちょうどの `86400` は通る
- 設定ファイル経由（`XDG_CONFIG_HOME` を差し替え）でも同じく弾かれること
- `README.md` の help 出力 3 ブロックが実出力と一字一句一致すること
  （`COLUMNS=80`）
- `uv run pytest tests` 146 passed（43 件増）、
  `ruff format` / `ruff check` / `basedpyright` / `mypy` すべて通過

## 分担の振り返り

**reviewer が最も効いた。** verifier が 4 回とも「全項目 PASS」を返した
のと同じ差分から、reviewer は毎回、次の穴を見つけている。

| 回 | reviewer が見つけたもの |
|---|---|
| 1 | `nan` / `inf` がすり抜ける。検証が `cycles` だけ `phases()` にある |
| 2 | frozen でないので構築後の代入ですり抜ける。例外文が `nan` に合わない |
| 3 | `CLAUDE.md` がアラームの検証に追随していない。`1e18` で `OverflowError` |
| 4 | 指摘なし |

**「動くか」と「良いか」が別だという前提が、そのまま出た。** verifier は
指示した項目を確かめる担当なので、指示に無い穴は原理的に見つけられない。
穴の種類を広げたのは全部 reviewer で、しかも毎回**実測してから**報告して
いる（`FloatRange.convert("nan")` が `nan` を返すこと、
`time.sleep(1e18)` が `OverflowError` になること、構築後の代入で
`next()` が返らないこと）。読んだだけの推測で終わっていない。

**見込みと食い違ったのは範囲のほう**で、分担ではない。見込みは
「0 と 0 サイクルを弾く」だったが、実際には `nan` / `inf`、frozen、
アラームの 3 オプション、`sleep` の上限まで広がり、実装が 4 回に分かれた。
料金も reviewer が 36% と、implementer（24%）より大きくなっている。
ただしこれは reviewer が高かったのではなく、**同じ種類の穴を出し切る
までレビューを繰り返した**結果で、掛けるべきところに掛かっている。

**次に同じ規模なら、同じ組み方でよい。** ただし 2 点変える。

1. **1 回目の依頼の時点で「同じ種類の穴を全部挙げてから実装する」と
   指示する。** 今回は「0 以下」だけを直させ、`nan` を後から足し、
   frozen を後から足し、上限を後から足した。実装・レビュー・検証を
   4 周した分、main と implementer のトークンが素直に 4 倍近く乗っている。
   最初に reviewer へ「この関数に渡ると壊れる値を、種類ごとに挙げよ」と
   1 回投げてから実装に入れば、周回を 2 回に減らせた見込み
2. **verifier は 4 回とも全 PASS で、料金は 3%。**安いので回数は
   減らさなくてよいが、**再現手順を毎回全部やり直させる必要は無かった**。
   2 回目以降は差分の分だけでよい

**implementer を Sonnet のままにした判断は正しかった。** 範囲と境界を
main が全部決めて渡したので、判断の要らない実装になっていた。
4 回とも指示どおりで、reviewer から実装そのものへの要修正は 1 件だけ
（`CLAUDE.md` の追随漏れ）だった。

分担の理由と各担当の報告は `archives/agents/TODO-012/` にある。
