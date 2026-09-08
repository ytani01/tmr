# TODO-012 reviewer report

対象: `git diff`（未コミット、7 ファイル）。コードは直していない。

**要修正: 0 件。検討: 5 件。好みの範囲: 1 件。**

## 検討

### 1. `nan` / `inf` が CLI もライブラリ層もすり抜ける（実測）

- 場所: `src/tmr/cli.py:109,117,125`（`FloatRange`）、`src/tmr/clock.py:24`
- 何が: `click.FloatRange(min=0, min_open=True).convert("nan")` は `nan` を
  そのまま返す（実測）。`TimerClock(nan)` も `nan <= 0` が False なので
  通る（実測）。`TimerClock.is_timeup` は `elapsed >= nan` が常に False な
  ので、`tmr pomodoro -w nan` はタイマーが永久に満了しない。`inf` も同じ。
- なぜ: TODO-012 の症状（固まる／終わらない）と同じ種類の穴が残る。
  TOML は `nan` / `inf` を float リテラルとして持つので、設定ファイルにも
  書ける（`tomllib.loads("work-time = nan")` が `nan` を返すのを実測）。
- ただし: `Q` は効くので、元の「アラームが止まらない」ほど悪くはない。
  手で打つ人も稀。今回の範囲外として別項目に立てるかは管理者判断。
- どうすると: `FloatRange` の後にコールバックで `math.isfinite()` を見るか、
  `TimerClock` の検証を `not math.isfinite(t_limit) or t_limit <= 0` にする。

### 2. 検証の置き場所が `cycles` だけ `phases()` にある

- 場所: `src/tmr/pomodoro.py:11-16, 22-32, 76-94`
- 何が: `cycles` は `phases()` で見ているが、`work_sec` / `break_sec` /
  `long_break_sec` は `PomodoroConfig` を作る時点では素通りする。
- なぜ: ライブラリとして使うと、`long_break_sec <= 0` は最初の長い休憩に
  入るまで（既定なら 4 サイクル後）気づけず、走っている途中で
  `Timer.__init__` → `TimerClock` の `ValueError` で落ちる。
  根拠は `PomodoroTimer.run()` / `_run_timer()` を読んだ結果。
  CLI からは `FloatRange` が弾くので、この経路は現れない。
- どうすると: `PomodoroConfig.__post_init__` に 4 項目の検証をまとめると、
  設定を作った時点で全部弾ける。副次的に `phases()` はジェネレータのままで
  よくなり、`_phases()` への分割も要らなくなる。

### 3. 不変条件を `__init__` でしか見ていない

- 場所: `src/tmr/clock.py:24-25`, `src/tmr/clock.py:79`（`rate`）
- 何が: `t_limit` は公開の可変属性で、`tests/test_view.py:143` や
  `tests/test_timer.py:299` が後から代入している。0 を代入されれば
  `rate` は再びゼロ除算する。
- なぜ: 「ライブラリ層でも防御する」という方針に対し、構築後は無防備。
- どうすると: `rate` 側にもガードを置くか、`t_limit` を property にして
  setter でも検証する。TODO-013 で `t_limit` の持ち方を触る予定なので、
  そこで一緒に決めるのが自然（今回の差分を止める理由にはならない）。

### 4. 追加した CLI テストが「なぜ 2 になったか」を見ていない

- 場所: `tests/test_cli.py:39-61`
- 何が: `result.exit_code == 2` だけを assert している。
- なぜ: usage error なら何でも 2 になる（オプション名の打ち間違い、引数の
  不足でも 2）。範囲チェックが消えても、別の理由で 2 になれば通ってしまう。
- どうすると: `"is not in the range" in result.output` を 1 つ足す。
- あわせて: TODO-012 の再現表にある負値（`timer -- -1` / `-c -1` /
  `-w -1`）が CLI テストに無い。実測ではいずれも exit 2 で
  正しいメッセージが出る（下記の確認欄）ので、テストに固定しておくとよい。

### 5. `CLAUDE.md` に、今回入った不変条件の記述が無い

- 場所: `CLAUDE.md` の「設計」節
- 何が: 「CLI で弾き、ライブラリ層でも防ぐ」という二重の作りが、設計の
  説明のどこにも書かれていない。
- なぜ: 次に触る人が `IntRange` / `FloatRange` を素の `int` / `float` に
  戻したり、`phases()` をジェネレータに戻したりしても気づけない。
- どうすると: 「Timer は 3 つに分かれている」か「戻り値でフェーズを制御
  する」の節に 1〜2 行足す（追記するかは管理者判断）。

## 好みの範囲

- `tests/test_clock.py:24-26` — `mock_time` フィクスチャは要らない
  （`TimerClock.__init__` は `time` に触れない）。`_ = mock_time` は
  リポジトリの既存の書き方（`tests/test_view.py:37` など）に沿っている
  ので害は無いが、外すと意図が読みやすい。`tests/test_pomodoro.py` 側と
  同じく `parametrize` にすると、対の 2 件が同じ形で並ぶ。

## 確認して問題が無かったこと（実測）

- 境界の向き: `FloatRange(min=0, min_open=True)` は `0` / `-1` を拒否し、
  `0.1` / `1e-9` を通す。`IntRange(min=1)` は `0` / `-1` を拒否し `1` を
  通す（`convert()` を直接呼んで確認）。
- CLI 実測: `timer 0` / `timer -- -1` / `-c 0` / `-c -1` / `--cycles=-1` /
  `-w 0` / `-w -1` は、いずれも exit 2 で
  `... is not in the range x>=1`（または `x>0`）が出る。固まらない。
- 設定ファイル経由でも `click` が `default_map` の値を型変換するので、
  `XDG_CONFIG_HOME` を差し替えて `[timer] minutes = 0` /
  `[pomodoro] cycles = 0` / `work-time = 0` を書くと exit 2 になる
  （`Invalid value for 'MINUTES': 0 is not in the range x>=1.` など）。
  **通常の利用でライブラリ層の `ValueError` がトレースバックとして
  出る経路は見つからなかった**（有限値に限れば。無限大・NaN は上記 1）。
- `phases()` の等価性: 呼び出し側 `PomodoroTimer.run()` は `for` 文なので、
  ジェネレータでもイテレータを返す関数でも同じ。既存の
  `test_phases_one_cycle` / `test_phases_repeats` が `next()` で回して
  通っている。型注釈は `Iterator[...]` のままで正しく、
  basedpyright / mypy とも 0 件。
- 例外の波及: `Timer.__init__` は `TimerClock` を `Terminal` より先に作る
  ので、端末に触る前に `ValueError` が出る。`TerminalContext.__exit__` は
  カーソルを戻してから例外を素通しする（抑制するのは
  `KeyboardInterrupt` だけ）ので、後始末に問題は無い。
- `ProgressBar` は `rate = val / self.total if self.total > 0 else 1.0`
  （`progress_bar.py:52`）で、元からゼロ除算しない。
- 例外メッセージ: `t_limit must be > 0: t_limit=0` /
  `cycles must be >= 1: cycles=0` は値が入っていて分かりやすい。
  開発者向けの `ValueError` なので英語でよい（利用者向けの
  `ClickException` が日本語なのは `config.py` のまま）。
- 小さい正の小数のリグレッションは、既存の `test_pomodoro_cli_exec`
  （`--work-time 0.1 --break-time 0.1` で exit 0）が担保している。
- 行長: 変更した全ファイルに 78 **文字**超えの行は無い（`ruff` はバイト数
  ではなく文字数なので、日本語コメントも含めて確認した）。
- `README.md` の help 出力は実出力と一致（`COLUMNS=80` で取り直して比較）。
  `timer` 側は `IntRange` にしても表示が変わらないことも実出力で確認した。
- 追試: `pytest tests` 103 passed / `ruff format --check` / `ruff check` /
  `basedpyright` / `mypy` すべて通る。
- 指示範囲外の変更は混ざっていない（7 ファイルとも TODO-012 の範囲内）。

## 補足

`TODO.md` の TODO-012 のチェックボックスと `archives/todo/` への移動は
未着手（管理者の作業なので指摘ではない）。
