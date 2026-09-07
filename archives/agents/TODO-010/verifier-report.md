# TODO-010 verifier 報告

依頼文 `archives/agents/TODO-010/verify-instructions.md` に沿って確認した。
コードは変更していない。

## 1. `TODO.md` のチェックボックス 5 つ

いずれも未チェックのまま（今回の確認のためと思われる）。実装状況は次のとおり。

1. **`TimerClock`（`clock.py`）を切り出す** — 済み。`src/tmr/clock.py`
   に `TimerClock` があり、`start()` / `tick()` / `toggle_pause()` /
   `forward()` / `backward()` / `remain` / `rate` / `is_timeup` を持つ。
   `time` 以外に依存しない（端末に依存しない）。
2. **`TimerView`（`view.py`）を切り出す** — 済み。`src/tmr/view.py` に
   `TimerView` があり、列の定義（`col_list()`）、幅に応じた省略
   （`display()` 内の削除ループ）、スタイル付け（`click.style`）を持つ。
3. **表示順と削除の優先順位を 1 箇所にまとめる** — 済み。
   `TimerCol.priority` が `col_list()` の各要素に付き、削除は
   `sorted(self.col.values(), key=lambda c: c.priority)` で
   priority の小さいものから行う。`COL_PRIORITY` の二重管理は無くなった。
   priority は date=1, time=2, elapsed=3, rate=4, limit=5, pbar=6,
   state=7, title=8, remain=9 で、依頼文にある削除順
   （date→time→elapsed→rate→limit→pbar→state→title→remain）と一致する。
   表示順（`col_list()` の並び）も date, time, title, limit, state,
   rate, elapsed, pbar, remain で一致する。
4. **`title` / `alarm_params` をデータクラスにする** — 済み。
   `view.py` に `@dataclass(frozen=True) class TimerTitle`
   （`text`, `color`, `width`）、`timer.py` に
   `@dataclass(frozen=True) class AlarmParams`（`count`, `sec1`, `sec2`）。
   `type AlarmParams = tuple[...]` の別名は `timer.py` から消えている
   （`grep -n "type AlarmParams"` で該当なし）。
5. **`PomodoroTimer.run()` からフェーズの並びをジェネレータに分離** —
   済み。`pomodoro.py` の `phases(config)` が
   `Iterator[tuple[TimerTitle, float]]` を無限に返し、`run()` は
   `for title, sec in phases(self.config): if self._run_timer(...): return True`
   という形。桁揃え `f"{tt:16s}"` は `TimerTitle(..., width=16)` +
   `TimerTitle.display_text` に移っている（`pomodoro.py` 側に文字列
   フォーマットは残っていない）。

**5 つとも実装済みと判断する。**

## 2. 依頼文 1〜7 の食い違い

- **`Timer` に `t_start` / `t_elapsed` / `is_paused` が残っていないこと**
  — 確認した。`grep -n "t_start\|t_elapsed\|self.is_paused" src/tmr/timer.py`
  は該当なし（`self.clock.is_paused` の参照のみ）。`t_start` /
  `elapsed` / `is_paused` は `clock.py` の `TimerClock` の属性として残る。
- **`type AlarmParams = tuple[...]` が消えていること** — 確認した。
  `timer.py` に無く、`AlarmParams` は dataclass として再定義されている。
- **CLI のオプションが変わっていないこと** — `uv run tmr timer --help`
  と `uv run tmr pomodoro --help` の実出力を `README.md` の該当節
  （76〜111 行）と突き合わせ、完全に一致することを確認した。
- **分割前のテストケースが新構成のどこかに残っていること** —
  `git show HEAD:tests/test_timer.py` の 21 個の `test_*` と、現在の
  `tests/test_timer.py`（19 個）・`tests/test_view.py`（12 個）・
  `tests/test_clock.py`（9 個）を突き合わせた。表示系のケース
  （`test_responsive_layout` / `test_rate_color` / `test_display_hours` /
  `test_display_pause_state` / `test_edge_cases_and_robustness` の
  `!?` 表示部分）は `test_view.py` へ、時刻計算系
  （`test_fn_forward` / `test_fn_backward` など）は
  `test_clock.py` / `test_timer.py`（委譲側）へ移っており、
  すべて対応先が見つかった。**欠落は見当たらない。**
- 依頼文 7（`CLAUDE.md` の更新）— 実装担当の報告では「やっていない」
  とあったが、`git diff CLAUDE.md` を見ると実際には 3 か所とも
  書き換えられている（「`Timer` は 3 つに分かれている」「表示は
  `col_list()` 1 つで決まる」「テスト」節のモック先の表）。
  内容は現在のコードと一致しており、TODO 番号も書かれていない。
  **誰がいつ更新したかは報告からは分からない**（implementer-report.md
  には記載が無く、reviewer の報告ファイルもまだ無い）。この点は
  判断が要る（下記）。

## 3. 検証コマンド

すべてリポジトリのトップで実行。

| コマンド | 結果 | 終了コード |
|---|---|---|
| `uv run pytest tests -q` | `97 passed` | 0 |
| `uv run ruff format --line-length 78 --diff src tests` | `24 files already formatted`（差分無し） | 0 |
| `uv run ruff check --extend-select I src tests` | `All checks passed!` | 0 |
| `uv run basedpyright src tests` | `0 errors, 0 warnings, 0 notes` | 0 |
| `uv run mypy src tests` | `Success: no issues found in 24 source files` | 0 |

すべて通った。`mise run` は使っていない。

## 4. 実機での表示確認

```
timeout 20 script -qec "stty rows 24 cols 100; uv run tmr pomodoro -w 0.02 -b 0.02 -l 0.02 -c 2" /dev/null | cat -v | tail -20
```

実行できた。出力（ANSI エスケープを含む生ログの抜粋）で確認した内容:

- フェーズ名 `WORK:1/2` が末尾に空白を足されて 16 桁で揃っている
  （`"WORK:1/2        "`、cyan・太字）
- 項目の並びは date, time, title, limit, rate, elapsed, pbar, remain
  の順（`state` は空文字のため表示されない。これは依頼文にある
  「並び順」と `state` 列自体の有無の話であり、`state` を含む定義順
  date, time, title, limit, **state**, rate, elapsed, pbar, remain
  と矛盾しない — 値が空の列は `display()` の最後のループで
  `if not col.use or not col.value: continue` により出力されない
  仕様どおり）
- 経過率に応じて `\x1b[37m`（white）→ `\x1b[33m`（yellow, 83.5%）→
  `\x1b[31m`（red, 100.0%）と色が変わっている

以上、確認できた。想像で補った箇所は無い。

## 変更ファイルの一覧（`git status` / `git diff --stat`）

```
 M CLAUDE.md
 M src/tmr/cli.py
 M src/tmr/pomodoro.py
 M src/tmr/timer.py
 M tests/test_cli.py
 M tests/test_config.py
 M tests/test_integration_alarm.py
 M tests/test_pomodoro.py
 M tests/test_timer.py
?? archives/agents/TODO-010/（依頼・報告ファイル一式）
?? src/tmr/clock.py
?? src/tmr/view.py
?? tests/test_clock.py
?? tests/test_view.py
```

依頼文の範囲（`clock.py` / `view.py` の新設、`timer.py` /
`pomodoro.py` / `cli.py` の変更、テスト一式、`CLAUDE.md`）と一致する。
`README.md` は変更されておらず、依頼文の「触らない」指示と合っている。
指示に無いファイルの変更は見当たらない。

## 確かめられなかったこと・判断が要る点

- **`CLAUDE.md` を誰が更新したか分からない。** implementer-report.md は
  「やっていない」と明記しているが、実際には更新済みで、内容も
  正しい。reviewer の報告ファイル
  （`archives/agents/TODO-010/reviewer-report.md` 相当）はまだ存在せず、
  誰の作業か記録が無い。実害は無いが、報告と実物の食い違いとして
  管理者に共有する。
- レビュー担当（`review-instructions.md` はあるが `reviewer-report.md`
  が無い）による、分岐・条件式の変更点のレビューが完了しているかは
  この報告の範囲外。挙動が変わる項目という位置づけなら、レビューの
  結果も別途確認が要る。

## 追加修正の確認

管理者が reviewer の指摘を受けて入れた 4 点（コードは直していない、確認のみ）。

1. **`timer.py` の `self.title` / `self.t_limit` 削除** —
   確認した。`grep -n "self.title\|self.t_limit\b" src/tmr/timer.py`
   は該当なし。`__init__` は `title` と `t_limit` を受け取るが、
   `TimerClock(t_limit)` と `TimerView(self.term, t_limit, title)` に
   渡すだけで、インスタンス属性としては保持していない。
2. **`main()` の 3 回の `self.view.display(...)` を `_display()` に統合** —
   確認した。`_display()`（`timer.py:186-192`）は
   ```python
   def _display(self) -> None:
       self.view.display(
           self.clock, is_active=self.is_active,
           alarm_active=self.alarm_active,
       )
   ```
   で、呼び出し箇所は 3 か所（メインループ中 `timer.py:222`、
   アラーム待ちループの中 `timer.py:240`、ループを抜けたあと
   `timer.py:246`）。3 か所とも引数は `self.clock` /
   `is_active=self.is_active` / `alarm_active=self.alarm_active` で
   同一であり、統合前に個別に呼んでいた 3 箇所の引数
   （前回確認時点のもの）と一致する。
3. **`view.py` の `TimerView.__init__` の `self.title` 削除** —
   確認した。`grep -n "self.title" src/tmr/view.py` は該当なし。
   `__init__` は `title` を受け取り、`self.col["title"].value` /
   `self.col["title"].color` を設定するのに使うだけで、属性としては
   保持していない。
4. **`tests/test_timer.py::test_init_defaults` の変更** — 確認した。
   ```python
   assert mock_view.call_args[0][2] == TimerTitle("Timer", "white")
   ```
   になっており、`TimerView(self.term, t_limit, title)` の第 3 引数
   （`title`）を見る形に合っている。

### 消した 3 属性がどこからも読まれていないこと

`grep -rn "\.title\b" src tests` で `TimerTitle` /
`title_color` / `title=` / `display_text` / コメント以外の一致は無し。
`self.t_limit`（`Timer` 側）についても
`grep -n "self.t_limit\b" src/tmr/*.py tests/*.py` で該当は無く、
`TimerClock.t_limit`（`clock.py`）と `TimerView` 内の別属性のみが
ヒットする（これらは削除対象ではない）。**`src` / `tests` のどこからも
読まれていないことを確認した。**

### 検証コマンド（前回と同じ 5 つ）

| コマンド | 結果 | 終了コード |
|---|---|---|
| `uv run pytest tests -q` | `97 passed` | 0 |
| `uv run ruff format --line-length 78 --diff src tests` | `24 files already formatted` | 0 |
| `uv run ruff check --extend-select I src tests` | `All checks passed!` | 0 |
| `uv run basedpyright src tests` | `0 errors, 0 warnings, 0 notes` | 0 |
| `uv run mypy src tests` | `Success: no issues found in 24 source files` | 0 |

すべて通った。

### 4 点以外の差分

`git status` / `git diff --stat` を見ると、変更ファイルの一覧は前回
確認時（本報告の冒頭の節）と同じ 9 ファイルの変更 + 4 ファイルの新規
（`clock.py` / `view.py` / `test_clock.py` / `test_view.py`）のみで、
新たに増減したファイルは無い。`CLAUDE.md` は「表示は `col_list()` 1 つで
決まる」節に、依頼どおり「`display()` でその列に値を入れる」という
1 文が足されているだけで、他の節に変更は無い。**4 点＋`CLAUDE.md` の
1 文以外に、意図しない差分は見当たらない。**
