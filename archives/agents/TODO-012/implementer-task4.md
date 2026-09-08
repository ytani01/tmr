# TODO-012 implementer への追加依頼 4（最終レビュー結果の反映）

最終レビューは `archives/agents/TODO-012/reviewer-report3.md`。
**要修正 1 件 + 検討 2 件**を取り込む。これが最後の依頼。

## I. `CLAUDE.md` をアラームの検証に追随させる（報告 3 の要修正 1）

今の 4 行（`CLAUDE.md:54-57`）は「`TimerClock` / `PomodoroConfig` でも
`ValueError` で弾く」としか書いておらず、`AlarmParams.__post_init__` に
触れていない。**アラームだけ境界が違う**（`count` / `sec1` / `sec2` は
0 を許す。時間・サイクル数は `> 0` / `>= 1`）ので、今の書き方だと
次に触る人が `--alarm-sec1 0` を弾く向きに「揃えて」しまいかねない。

- 4 行のうち `TimerClock` / `PomodoroConfig` に `AlarmParams` を足す
- **アラームの回数と間隔は 0 を許す**（鳴らさない／間を空けない）ことと、
  J で足す上限にも触れる 1〜2 行を足す
- **長く書かない。** 既存の書き方（である調、名詞止め、簡潔）に合わせる

## J. アラームの間隔に上限を足す（報告 3 の検討 2）

検証が「有限かつ >= 0」なので `1e18` が通る。一方
`time.sleep(1e18)` は `OverflowError: timestamp out of range for
platform time_t` になり（reviewer が実測）、`thr_alarm()` は daemon
スレッドなので落ちると `alarm_active` が True のまま残る。

**上限は 1 日（86400 秒）とする。** アラームの「鳴らす間隔」として
現実的に十分で、`timefmt.py` の `SEC_MIN` / `MIN_HOUR` から表せる。

- `src/tmr/timefmt.py` に 1 日の秒数の定数を足すか、既存の
  `SEC_MIN` / `MIN_HOUR` から `src/tmr/timer.py` 側で組み立てるか、
  **既存の書き方に馴染む方**を選ぶ。生の `86400` を直接書かない
- `src/tmr/cli.py` — `--alarm-sec1` / `--alarm-sec2` を
  `click.FloatRange(min=0, max=<上限>)` にする。
  `--alarm-count` は `time.sleep()` に渡らないので**上限は足さない**
  （`IntRange(min=0)` のまま）
- `src/tmr/timer.py` — `AlarmParams.__post_init__` の `sec1` / `sec2` の
  検証に上限を足す。メッセージも上限が分かる文にする
- テストを足す — CLI で上限超え（例: `--alarm-sec1 1e18`）が終了コード 2 に
  なること、`AlarmParams` の上限超えが `ValueError` になること、
  **上限ちょうどは通ること**

## K. 「0 を許す」テストを厚くする（報告 3 の検討 3）

`tests/test_cli.py` の `test_timer_alarm_count_and_sec1_zero_allowed` は
`--alarm-sec2 0` を見ておらず、また `Timer` をモックしているので
**どんな `AlarmParams` が渡ったか**を確かめていない。

- `--alarm-sec2 0` も加える
- `MockTimer.call_args` から、渡った `AlarmParams` が
  `count=0` / `sec1=0.0` / `sec2=0.0` であることを確かめる。
  境界の向きを取り違えた変更（`min_open=True` を付ける等）を捕まえるため

## 完了条件

- I〜K がすべて済んでいる
- `uv run pytest tests` が全て通る
- lint が通る（`ruff format` / `ruff check --fix --extend-select I` /
  `basedpyright` / `mypy`。`mise run` は使わない）
- `uv run tmr timer 1 --alarm-count 0 --alarm-sec1 0 --alarm-sec2 0` が通る
- **`uv run tmr timer --help` の出力がまた変わる**（`--alarm-sec1` /
  `--alarm-sec2` に上限が付く）。`COLUMNS=80` で実出力を取り直して
  `README.md` を必ず合わせる
- 行長 78 文字、ログ規約を守る

## やらないこと

- コミットしない。`TODO.md` は触らない
- タイマー本体（`timer` の分数、`-w` / `-b` / `-l`）に上限は足さない。
  これらは `time.sleep()` に渡らず `OverflowError` にならないので、
  今回の範囲外
- 報告 1 の 3（`t_limit` を後から代入されたときの防御）は TODO-013 に残す
- 報告 3 の「好みの範囲」（`for name in (...)` + `getattr` の共通化）は
  reviewer 自身が「現状でよい」としているので触らない

## 報告

`archives/agents/TODO-012/implementer-report4.md` に書く。返事は 5 行以内。
