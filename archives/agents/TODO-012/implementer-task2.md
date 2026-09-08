# TODO-012 implementer への追加依頼（レビュー結果の反映）

先の実装に対する reviewer の報告は
`archives/agents/TODO-012/reviewer-report.md`。**要修正 0 件**なので、
今の差分を巻き戻す必要は無い。以下は管理者が取り込むと決めた 4 件。

## A. 検証を `PomodoroConfig.__post_init__` にまとめる（報告の 2）

今は `cycles` だけ `phases()` で見ていて、`work_sec` / `break_sec` /
`long_break_sec` は素通りする。ライブラリとして使うと
`long_break_sec <= 0` が既定 4 サイクル後まで気づけない。

- `PomodoroConfig` に `__post_init__` を足し、**4 項目すべて**を検証する
  - `work_sec` / `break_sec` / `long_break_sec` — 0 より大きく、かつ有限
    （下の B の `math.isfinite` を含む）
  - `cycles` — 1 以上
  - どのフィールドが不正かが分かるメッセージにする
- これで `phases()` 側の検証は要らなくなる。**`phases()` を元の
  ジェネレータに戻し、`_phases()` への分割は取り消す**（分割は
  `cycles` 検証のためだけに入れたもの）
- `tests/test_pomodoro.py` の `phases()` の `ValueError` テストは、
  `PomodoroConfig(...)` の構築時に `ValueError` になるテストへ置き換える。
  `work_sec` / `break_sec` / `long_break_sec` / `cycles` の**それぞれ**に
  ついて 0 と負値を見る

## B. `nan` / `inf` も弾く（報告の 1）

`FloatRange(min=0, min_open=True)` は `nan` をそのまま通し、
`TimerClock(nan)` も `nan <= 0` が False なので通る。`is_timeup` が
`elapsed >= nan` で常に False になり、**タイマーが永久に満了しない**。
`inf` も同じ。TOML にも `nan` / `inf` は書けるので設定ファイル経由でも入る。

- `src/tmr/clock.py` — `TimerClock.__init__` の検証を
  `not math.isfinite(t_limit) or t_limit <= 0` に広げる
- `src/tmr/pomodoro.py` — 上の A の `__post_init__` でも同様に有限性を見る
- `src/tmr/cli.py` — `pomodoro` の `-w` / `-b` / `-l` に、`FloatRange` の
  後段で有限性を見るコールバックを足す（`click.BadParameter` を上げる）。
  **3 つで同じ処理なので、共通のコールバック関数を 1 つ作って使い回す**。
  `timer` の `minutes` と `-c` は `int` なので `nan` / `inf` は入らない。
  対象外
- テストを足す — CLI で `-w nan` / `-w inf` / `-b nan` / `-l inf` が
  usage error（終了コード 2）になること、`TimerClock(float("nan"))` /
  `TimerClock(float("inf"))` と `PomodoroConfig` の対応するフィールドが
  `ValueError` になること

## C. CLI テストを強化する（報告の 4）

`tests/test_cli.py` の追加分が `result.exit_code == 2` しか見ていない。
usage error は打ち間違いでも 2 になるので、範囲チェックが消えても通る。

- 出力に `"is not in the range"` が含まれることも assert する
  （B のコールバック由来のエラーは別のメッセージになるので、そちらは
  そのメッセージに合わせる）
- **負値のケースを足す** — `tmr timer -- -1`、`tmr pomodoro -c -1`、
  `tmr pomodoro -w -1`

## D. `CLAUDE.md` に、二重の防御を書く（報告の 5）

「CLI で弾き、ライブラリ層でも防ぐ」作りが設計の説明のどこにも無いので、
次に触る人が `IntRange` / `FloatRange` を素の `int` / `float` に戻しても
気づけない。

- 「設計」節（「Timer は 3 つに分かれている」あたり）に **2〜4 行**足す。
  CLI の型で弾くことと、`TimerClock` / `PomodoroConfig` でも不正な値を
  `ValueError` で弾くこと、`nan` / `inf` も対象であること、
  その理由（ライブラリとして直接使う経路があるため）
- **長く書かない。** 既存の書き方（である調、簡潔）に合わせる

## 完了条件

- A〜D がすべて済んでいる
- `uv run pytest tests` が全て通る
- lint が通る:
  ```
  uv run ruff format --line-length 78 src tests
  uv run ruff check --fix --extend-select I src tests
  uv run basedpyright src tests
  uv run mypy src tests
  ```
- `uv run tmr pomodoro -w 0.1 -b 0.1 -l 0.1 -c 2` が**通る**こと
  （小さい正の小数を弾いてはいけない）
- `uv run tmr pomodoro --help` の出力が変わっていないか確認し、
  変わっていれば `README.md` を実出力に合わせる
- 行長 78 文字、ログ規約を守る

## やらないこと

- コミットしない。`TODO.md` は触らない
- `t_limit` を後から代入されたときの防御（報告の 3）は **TODO-013 で扱う**
  ので、今回は手を入れない
- 報告の「好みの範囲」（`tests/test_clock.py` の `mock_time`）は任意。
  A〜D のついでに直すなら構わないが、無理に触らなくてよい

## 報告

`archives/agents/TODO-012/implementer-report2.md` に、変更点・検証結果・
残る懸念を書く。返事は 5 行以内。
