# TODO-012 implementer への依頼

## 目的

`tmr` で 0 以下の時間・サイクル数を指定したときの破綻を直す。

再現済みの現象（すべて確認済み。再現し直す必要は無い）:

| 指定 | 現象 |
|---|---|
| `tmr timer 0` | `TimerClock.rate` で `ZeroDivisionError` |
| `tmr timer -- -1` | 即満了扱いでアラームが鳴り続け、止まらない |
| `tmr pomodoro -c 0` / `-c -1` | `phases()` が何も yield せず `while True` を回り続けて固まる |
| `tmr pomodoro -w 0` | `timer 0` と同じ `ZeroDivisionError` |

## 決まった方針

**CLI で弾き、ライブラリ層でも防御する。** 0 を「即満了」として動かすことはしない。

## 変更範囲

### 1. `src/tmr/cli.py` — click の型で弾く

| 対象 | 変更 |
|---|---|
| `timer` の引数 `minutes` | `type=int` → `click.IntRange(min=1)` |
| `pomodoro` の `-w` / `-b` / `-l` | `type=float` → `click.FloatRange(min=0, min_open=True)` |
| `pomodoro` の `-c` | `type=int` → `click.IntRange(min=1)` |

`-w 0.1` のような小数は通ること（`CLAUDE.md` の動作確認コマンドで使う）。

### 2. ライブラリ層の防御

- `src/tmr/clock.py` の `TimerClock.__init__` — `t_limit <= 0` なら `ValueError`。
  メッセージに実際の値を入れる。これで `rate` のゼロ除算も、負値による
  「即満了でアラームが止まらない」も同時に塞がる
- `src/tmr/pomodoro.py` の `phases()` — `config.cycles < 1` なら `ValueError`。
  ジェネレータなので**関数の先頭で判定してもすぐには実行されない**点に注意する。
  最初の `next()` で確実に上がる形にすること（判定を行う普通の関数から
  ジェネレータを返す、など）。無限ループに入る前に落ちればよい
- `Timer.__init__` は `TimerClock` を作るので、そこで自動的に弾かれる。
  `Timer` 側に重ねてチェックは足さない

### 3. テスト

- `tests/test_clock.py` — `TimerClock(0)` と `TimerClock(-1)` が `ValueError`
- `tests/test_pomodoro.py` — `cycles=0` / `cycles=-1` の `phases()` が `ValueError`
  （**テストが固まらないよう、必ずタイムアウトの効く形で書く**）
- `tests/test_cli.py` — `tmr timer 0`, `tmr pomodoro -c 0`, `tmr pomodoro -w 0` が
  `CliRunner` で終了コード 2（click の usage error）になること

既存テストは全て正の値を使っているので影響は無いはず。

### 4. `README.md`

`IntRange` / `FloatRange` にすると help 出力に `[x>=1]` のような範囲表示が
入る。`README.md` に載せている help 出力を、**実際の出力を取り直して**
合わせる（`CLAUDE.md` の「オプションを変えたら README.md の help 出力も直す」）。

## 完了条件

- 上の 4 点がすべて済んでいる
- `uv run pytest tests` が全て通る
- lint が通る:
  ```
  uv run ruff format --line-length 78 src tests
  uv run ruff check --fix --extend-select I src tests
  uv run basedpyright src tests
  uv run mypy src tests
  ```
- 行長 78 文字を守る
- ログ規約（`CLAUDE.md`）を守る

## やらないこと

- コミットしない（管理者が行う）
- `TODO.md` は触らない
- 範囲外のリファクタリングをしない

## 報告

`archives/agents/TODO-012/implementer-report.md` に、変更点・検証結果・
残る懸念を書く。返事は「終わったか・報告ファイルのパス・判断が要る点」の
5 行以内にすること。
