# TODO-012 implementer への追加依頼 3（2 回目のレビュー結果の反映）

2 回目の reviewer 報告は `archives/agents/TODO-012/reviewer-report2.md`。
**要修正 0 件**なので巻き戻しは不要。以下 4 件を取り込む。

## E. `PomodoroConfig` を frozen にする（報告 2 の 1）

`__post_init__` に検証を集約したので「作れなければ安全」になったが、
dataclass は既定で可変なので構築後に `config.cycles = 0` と代入すると
`phases()` が元どおり固まる（reviewer が実測）。

- `PomodoroConfig` を `@dataclass(frozen=True)` にする。
  前例は `src/tmr/timer.py` の `AlarmParams`
- `src` / `tests` に `PomodoroConfig` のフィールドへ代入している箇所は
  無い（reviewer が grep 済み）が、**自分でも確かめてから**変える
- 構築後の代入が `dataclasses.FrozenInstanceError` になるテストを足す

## F. 例外メッセージを直す（報告 2 の 3）

`TimerClock(float("nan"))` が `t_limit must be > 0: t_limit=nan` になり、
`isfinite` も見ているのにメッセージが「> 0」しか言っていない。

- `src/tmr/clock.py` と `src/tmr/pomodoro.py` の `ValueError` の文を、
  **有限であることと 0 より大きいことの両方**が分かる文にする
  （例: `t_limit must be a finite number > 0: t_limit=nan`）
- 既存テストがメッセージを見ているなら合わせる

## G. 小さな注釈を足す（報告 2 の 2 と「好みの範囲」）

- `PomodoroConfig.__post_init__` の
  `for name in ("work_sec", "break_sec", "long_break_sec")` に、
  **「時間のフィールドを足したらここにも足す」**ことが分かる
  コメントを 1 行足す
- `cli.py` の `_reject_non_finite` の docstring に、`ctx` / `param` を
  使わないのは `click` のコールバック規約で受けているだけだと分かる
  一言を足す
- **どちらも 1 行。長く書かない**

## H. アラームの 3 オプションにも同じ検証を入れる（報告 2 の 4）

`--alarm-count` / `--alarm-sec1` / `--alarm-sec2` だけ素の `int` /
`float` のままで、負値も `nan` も通る。

**実害があるのは `sec1` / `sec2`。** `time.sleep(-1.0)` /
`time.sleep(nan)` が `ValueError` を投げると `thr_alarm()` の
daemon スレッドがそこで死に、末尾の `self.alarm_active = False`
（`src/tmr/timer.py:337`）に到達しない。`Timer.main()` の
`while self.alarm_active` が抜けられなくなる。

`count` は `range(count)` なので 0 でも負でも「鳴らさない」だけで
固まらないが、意味の通る範囲に揃える。

境界は次のとおり。**`count=0`（鳴らさない）と `sec=0`
（間を空けずに鳴らす）はどちらも意味が通るので、0 は許す。**
0 を弾かないこと（`-w` などとは境界が違う）。

| 対象 | CLI の型 | 補足 |
|---|---|---|
| `--alarm-count` | `click.IntRange(min=0)` | 0 は「鳴らさない」 |
| `--alarm-sec1` | `click.FloatRange(min=0)` + `_reject_non_finite` | `min_open` は付けない |
| `--alarm-sec2` | `click.FloatRange(min=0)` + `_reject_non_finite` | 同上 |

- `src/tmr/cli.py` — `timer` の 3 オプションを上の型にする。
  コールバックは既存の `_reject_non_finite` を使い回す
- `src/tmr/timer.py` — `AlarmParams`（既に frozen）に `__post_init__` を
  足し、`count >= 0`、`sec1` / `sec2` が**有限かつ 0 以上**であることを
  検証して `ValueError`。メッセージは F と同じ書き方に揃える
- テストを足す — CLI で `--alarm-count -1`、`--alarm-sec1 -1`、
  `--alarm-sec1 nan`、`--alarm-sec2 inf` が終了コード 2 になること。
  `AlarmParams` の異常値が `ValueError` になること。
  **`--alarm-count 0` と `--alarm-sec1 0` は通ること**も確認する
- `AlarmParams` を作る既存のテスト（`tests/test_integration_alarm.py`
  など）が壊れないか見る

## 完了条件

- E〜H がすべて済んでいる
- `uv run pytest tests` が全て通る
- lint が通る（`ruff format` / `ruff check --fix --extend-select I` /
  `basedpyright` / `mypy`。`mise run` は使わない）
- `uv run tmr pomodoro -w 0.1 -b 0.1 -l 0.1 -c 2` が通る
- `uv run tmr timer 1 --alarm-count 0` が通る
- **`uv run tmr timer --help` の出力が変わる**（`IntRange` /
  `FloatRange` にすると `[x>=0]` が付く）。実出力を取り直して
  `README.md` の `timer --help` を必ず合わせる。
  `COLUMNS=80` で取ること
- 行長 78 文字、ログ規約を守る

## やらないこと

- コミットしない。`TODO.md` は触らない
- 報告 1 の 3（`t_limit` を後から代入されたときの防御）は TODO-013 に残す

## 報告

`archives/agents/TODO-012/implementer-report3.md` に書く。返事は 5 行以内。
