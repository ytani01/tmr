# TODO-012 reviewer report 2（追加実装のレビュー）

対象: `implementer-report2.md` の A〜D にあたる追加分。
（報告 1 の指摘 3 は TODO-013 へ回すと決まったので見ていない。）

**要修正: 0 件。検討: 4 件（うち 1 件は範囲外）。好みの範囲: 1 件。**

## 検討

### 1. `cycles < 1` の無限ループは、構築後の代入で再発する（実測）

- 場所: `src/tmr/pomodoro.py:12`（`@dataclass`）、`src/tmr/pomodoro.py:32-`
  （`phases()`）
- 何が: `PomodoroConfig` は frozen ではないので、

  ```python
  c = PomodoroConfig(10.0, 20.0, 30.0, 1)
  c.cycles = 0          # 通る
  next(phases(c))       # 返ってこない
  ```

  を実測した（`timeout 15` で kill されるまで `next()` が返らない）。
  `phases()` はループのたびに `config.cycles` を読むので、走行中の
  書き換えも効いてしまう。
- なぜ: 検証を `__post_init__` に集約したことで「作れなければ安全」に
  なったが、dataclass は既定で可変なので不変条件が構築時にしか効かない。
  TODO-012 の症状（何も yield せずに `while True` を回る）が、
  ライブラリ利用者の手元で 2 行で再現する。CLI からは起きない。
- どうすると: `@dataclass(frozen=True)` にすれば閉じられる。
  同じリポジトリの `AlarmParams`（`src/tmr/timer.py:18`）が既に
  `@dataclass(frozen=True)` なので、書き方の前例もある。
  `src` と `tests` に `PomodoroConfig` のフィールドへ代入している箇所は
  無い（grep 実測）ので、そのまま frozen にできる見込み。
  `__post_init__` は自分では代入しないため frozen と両立する。

### 2. `__post_init__` の 3 つ組は、フィールドを足したときに漏れる

- 場所: `src/tmr/pomodoro.py:19-26`
- 何が: `for name in ("work_sec", "break_sec", "long_break_sec")` と
  名前を文字列で並べているので、時間のフィールドを足したときに
  ここへ足し忘れても静かに素通りする。
- なぜ: 「作れなければ安全」を頼りにしている以上、検証の網羅が
  クラス定義から自動で追随しないのは弱い。ただし名前を打ち間違えた
  場合は `AttributeError` になり、追加された 14 通りのテストで気づける。
- どうすると: 数が増えないうちは今のままでも読みやすい。足すなら
  「フィールドを足したらここも足す」ことが分かる一言をコメントで
  残しておくと親切（`dataclasses.fields()` を回す形は、`cycles` だけ
  条件が違うので、かえって読みにくくなりそう）。重要度は低い。

### 3. `TimerClock` のメッセージが `nan` / `inf` のときにずれる

- 場所: `src/tmr/clock.py:25`
- 何が: `TimerClock(float("nan"))` は
  `t_limit must be > 0: t_limit=nan` になる。条件は `isfinite` も
  見ているのに、メッセージは「> 0」しか言っていない。
- なぜ: `nan` は「> 0 ではない」と言われても腑に落ちない。CLI 側は
  範囲エラー（`x>0`）と `must be finite` を分けているので、
  ライブラリ側だけ 1 文で兼ねている形になっている。
- どうすると: `t_limit must be a finite number > 0: ...` のように
  1 語足す。`PomodoroConfig` 側（`pomodoro.py:23`）も同じ。

### 4. 範囲外の気づき: アラーム関連のオプションは今も素通し

- 場所: `src/tmr/cli.py:58-79`（`--alarm-count` / `--alarm-sec1` /
  `--alarm-sec2`）
- 何が: この 3 つだけ素の `int` / `float` のままで、負値も `nan` も
  通る。`time.sleep(-1.0)` は
  `ValueError: sleep length must be non-negative`、
  `time.sleep(nan)` は `ValueError: Invalid value NaN (not a number)`
  になることを実測した。`Timer.thr_alarm()` は daemon スレッドなので、
  そこで落ちると `alarm_active` が True のまま残る
  （**スレッドが落ちた後の画面の見え方までは未確認**）。
- なぜ: TODO-012 と同じ種類の穴だが、**今回の項目の範囲外**。
  今の差分を止める理由にはならない。別項目に立てるかは管理者判断。

## 好みの範囲

- `src/tmr/cli.py:21-27` — `_reject_non_finite(ctx, param, value)` は
  `ctx` / `param` を使わない。`click` のコールバック規約で受けるだけ
  だと docstring に一言あると、未使用引数が意図的だと分かる
  （テスト側では `_ = mock_time` と明示する書き方をしている）。
  型注釈が無いのは `cli.py` の他の関数と揃っているので問題ない。

## 確認して問題が無かったこと（実測）

- **設定ファイル由来の値にもコールバックが効く**。`XDG_CONFIG_HOME` を
  差し替えて確認した。
  - `[pomodoro] work-time = nan` →
    `Error: Invalid value for '--work-time' / '-w': must be finite: nan`
    （exit 2）
  - `[pomodoro] long-break-time = inf` →
    `Error: Invalid value for '--long-break-time' / '-l': must be finite: inf`
  - **パラメータ名（長短どちらのオプション名も）が出る。**
    `click` が `augment_usage_errors` でパラメータを補うため、
    `BadParameter` に `param_hint` を渡していなくても名前が出る
- コールバックは `FloatRange` の後段で動く。`nan` は範囲チェックを
  素通りしてコールバックに届く（前回 `FloatRange.convert("nan")` が
  `nan` を返すことを実測済み）ので、二段にしたのは妥当。
- `PomodoroConfig.__post_init__` の検証は過不足なし。4 フィールドすべてを
  覆い、`work_sec` / `break_sec` / `long_break_sec` は「有限かつ > 0」、
  `cycles` は「>= 1」で、CLI 側の `x>0` / `x>=1` と向きが一致している。
- **小さい正の小数は通る**（前回 OK だった点が崩れていない）。
  `-w 0.1 -b 0.1 -l 0.1 -c 1` は exit 0 で
  `PomodoroConfig(work_sec=6.0, break_sec=6.0, long_break_sec=6.0,
  cycles=1)` が渡る。`-w 1e-9` も通る。`TimerClock(0.001)` も通る。
- `phases()` をジェネレータに戻したことによる退行は、CLI と
  `PomodoroConfig` 経由では無い（`cycles < 1` の config が作れないため）。
  既存の `test_phases_one_cycle` / `test_phases_repeats` も通る。
  ただし構築後の代入は上記 1 のとおり。
- 追加テストは分岐を突いている。CLI テストは exit code だけでなく
  `is not in the range` / `must be finite` を見ており、範囲チェックと
  コールバックのどちらで落ちたかを区別できる。`timer` の負値で `--` を
  挟んでいるのも正しい（挟まないと `No such option: -1` という別の
  エラーになることを前回実測している）。`PomodoroConfig` のテストは
  4 フィールド × 異常値の 14 通りで、名前の打ち間違いも拾える。
- `CLAUDE.md:54-57` の 4 行は事実として正しい。`IntRange` は `minutes` と
  `--cycles`、`FloatRange` + コールバックは `-w` / `-b` / `-l`、
  ライブラリ側は `TimerClock` と `PomodoroConfig` で、記述と実装が
  一致している。int には `nan` / `inf` が存在しないので
  「0 以下・`nan`・`inf` の時間やサイクル数」はやや大づかみだが、
  誤りではない。文体（名詞止め）・長さ（78 文字以内）・
  `（TODO-012）` の付け方も既存の箇条書きに揃っている。置き場所も、
  `TimerTitle` / `AlarmParams` の説明が並ぶ節の末尾で妥当。
- `README.md` の `pomodoro --help` は実出力と一致（`COLUMNS=80` で
  取り直して diff、差分なし）。コールバックはヘルプ表示を変えない。
- 前回問題が無かった点は崩れていない: 0 / 負値の CLI 拒否、設定ファイル
  経由の拒否、`Timer.__init__` が `Terminal` より先に `TimerClock` を
  作ること、`ProgressBar` のゼロ除算ガード。
- 追試: `pytest tests` 125 passed / `ruff format --check` /
  `ruff check` / `basedpyright` 0 件 / `mypy` OK。
- 行長: 変更した全ファイルに 78 **文字**超えの行は無い
  （`CLAUDE.md` の 3 行目・175-176 行目は今回の変更より前からある行）。
- 指示範囲外の変更は混ざっていない。
