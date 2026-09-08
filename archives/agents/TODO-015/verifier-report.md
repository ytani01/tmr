# TODO-015 verifier 報告

## 検証環境

- `uv run pytest tests` → `150 passed`、終了コード 0
- `uv run ruff format --line-length 78 --check src tests` →
  `24 files already formatted`、終了コード 0
- `uv run ruff check --extend-select I src tests` →
  `All checks passed!`、終了コード 0
- `uv run basedpyright src tests` → `0 errors, 0 warnings, 0 notes`、終了コード 0
- `uv run mypy src tests` → `Success: no issues found in 24 source files`、
  終了コード 0

すべて通過。`src` / `tests` は変更されていないので、この結果は
リグレッションが無いことの確認（想定どおり）。

## 変更ファイルの範囲

```
git status
  modified:   README.md
  untracked:  archives/agents/TODO-015/
  untracked:  docs/Developer.md
  untracked:  docs/User.md
```

指示（design.md・TODO.md）どおり。`src/` `tests/` `TODO.md` に手は
入っていない。`git diff --stat` は `README.md | 157 +++---------` の 1 件のみ。

## 1. 書いたとおりに試して一致を見る

- **確認した・問題なし**: `README.md` の Install（`mise trust` →
  `mise run build` → `uv tool install -U .`）は `mise.toml` の
  `[tasks.build]` および `mise` の組み込みコマンド `mise trust` と
  矛盾しない。`Requirement` の Python 3.13+ は `pyproject.toml` の
  `requires-python = ">=3.13"` と一致。
- **確認した・問題なし**: `docs/User.md` に貼られた 3 つの help 出力
  （`tmr --help` / `tmr timer --help` / `tmr pomodoro --help`）を
  `COLUMNS=80 uv run tmr ... --help` で再取得し、`diff` で 1 文字も
  差が無いことを確認した。
- **確認した・問題なし**: `docs/User.md` の COMMAND LIST は
  `Timer(enable_next=True).fn_help()` の実出力と完全一致
  （末尾の空行 1 個の差のみ。出力側の仕様で、文書側の問題ではない）。
- **確認した・問題なし**: コマンド例を実行して確かめた。
  - `tmr timer 3 -t "Tea" -c green` → エラー無く起動し、タイマーが
    正常に進んだ（`q` で終了、終了コード 0）。オプションの綴りは正しい。
  - `tmr timer 5 --alarm-count 0` → 起動して正常に進行（`q` の
    タイミングが合わずタイムアウトで打ち切ったが、出力にエラーは無い。
    オプション自体は正しく受理されている）。
  - `tmr pomodoro -w 0.1 -b 0.1 -c 2` → 同上、エラー無く起動した。
- **確認した・問題なし**: `docs/Developer.md` の開発コマンド
  （`uv run pytest tests`、lint 4 本）はすべて上記のとおり実際に通った。

## 2. 画面の実例の再現

`elapsed=630` / `t_limit=1500` / 日時 `2026-09-08 14:03:21` /
title `Timer` で `TimerView.display()` を直接呼び、`blessed.Terminal` を
`MagicMock`（`term.width` に数値）にして確かめた。

- **確認した・問題なし**: 「画面の見方」の枠内 1 行（幅 70 相当）は
  実際の出力と 1 文字も違わない。
- **確認した・問題なし**: 指示線の位置（`date`=2, `time`=13, `title`=22,
  `limit`=28, `rate`=33, `elapsed`=39, `pbar`=46, `remain`=66）を、
  実際にレンダリングした文字列中の各項目の開始位置と突き合わせ、
  すべて一致することを確認した。
- **確認した・問題なし**: 「端末の幅が狭いとき」の 7 行（70/50/40/30/25/15/10）を
  同じ条件で再現し、`docs/User.md` の該当 7 行と `diff` で完全一致した。

## 3. mermaid の描画

`@mermaid-js/mermaid-cli` 11.17.0 に
`-p <puppeteer設定ファイル（executablePath: /usr/bin/chromium, args:
--no-sandbox）>` を渡して、README 1 枚・Developer.md 4 枚すべてを
`.svg` にレンダリングした。5 枚とも `Generating single mermaid chart` で
正常終了し、SVG の `aria-roledescription` がそれぞれ `flowchart-v2` ×4、
`stateDiagram` ×1 で、エラー図（`error-icon` 等）になっていないことを
確認した。

- **確認した・問題なし**（5 枚すべて）。

## 4. 文書の記述と実装の突き合わせ

- **確認した・問題なし**: 「落とす順」の表
  （date→time→elapsed→rate→limit→pbar→state→title→remain）は
  `view.py` `col_list()` の `priority`（1,2,3,4,5,6,7,8,9）と完全一致。
- **確認した・問題なし**: 「経過率に応じて色」80%/95% は
  `TimerView.PERCENT_COLOR = {"white": 0, "yellow": 80, "red": 95}` と一致。
- **確認した・問題なし**: 「色が変わるのは state/rate/elapsed/pbar/remain」は
  `col_list()` で `rate_color=True` が付いている列
  （`state` `rate` `elapsed` `pbar` `remain`）と一致。
  `title` `limit` `date` `time` には付いていない。
- **確認した・問題なし**: アラームの説明。`thr_alarm()` は
  `for _ in range(count): for s in [sec1, sec2]: ...` なので、
  「1 回の繰り返しで 2 回鳴らす」「`--alarm-count 0` で `range(0)` になり
  鳴らさない」は実装と一致。上限は `AlarmParams.__post_init__` の
  `MAX_ALARM_SEC = SEC_DAY`（1 日）で一致。
- **確認した・問題なし**: 早送り・巻き戻し。`TimerClock.forward()` は
  `t_start = max(t_start - sec, t_cur - t_limit)` で `elapsed` が
  `t_limit` を超えない。`backward()` は `t_start = min(t_start + sec,
  t_cur)` で `elapsed` が 0 未満にならない。
  「設定時間の範囲を超えない」の記述と一致。
- **確認した・問題なし**: ポモドーロの説明。`pomodoro.py` の `phases()`
  は `while True` で無限にフェーズを返し、`-c`（`cycles`）は
  1 巡の作業回数を決めるだけ。`[N]`（`enable_next=True` のときの
  next）で次のフェーズへ、`[Q]`（`fn_quit` → `quit_by_quitcmd=True`）
  でポモドーロ全体が終わる、`PomodoroTimer.run()` は
  `Timer.main()` が `True` を返したときだけ `for` を抜ける。
  README / User.md の記述と一致。誤った旧説明
  （「quit すると次のフェーズに移ります」「強制終了してください」）は
  3 文書のどこにも残っていない。
- **確認した・問題なし**: `Developer.md`「表示の決まり方」の表と
  `col_list()` の定義（name・priority）が完全一致。「値の検証」の節
  （二重の検証、アラームの回数・間隔だけ 0 を許す、上限 1 日）も
  `AlarmParams` / `TimerClock` / `PomodoroConfig` の `__post_init__` と
  一致。
- **確認した・問題なし**: `Developer.md`「テスト」の patch 先の表を
  `tests/test_timer.py` / `test_view.py` / `test_clock.py` の
  `@patch` 対象と突き合わせ、記載どおりであることを確認した。

## 5. TODO-015 の完了条件

- **確認した・問題なし**: design.md の節構成（README 9 節、User.md 8 節、
  Developer.md 11 節）がすべて入っている。README には明示の
  「ライセンス」見出しは無いが、末尾に `---` と著作権表記があり、
  design.md の「ライセンス表記」に相当する内容はある。
- **確認した・問題なし**: 図 1〜6（mermaid 5 枚＋テキスト図 2 枚）が
  すべて入っている。
- **確認した・問題なし**: 旧 README にあった「COMMAND LIST」
  「各サブコマンドの help 出力」「設定ファイル」の節は README に
  残っておらず、`docs/User.md` へ移っている
  （`grep` で `COMMAND LIST` / `Usage: tmr` が README に無いことを確認）。
- **確認した・問題なし**: 誤った説明「quit すると次のフェーズに
  移ります／強制終了してください」は 3 文書のどこにも無い。
- **重複について（好み・報告のみ）**: `docs/User.md`「端末の幅が狭いとき」の
  「落ちる順」の表（priority 番号は書かず名前だけを順に並べたもの）と、
  `docs/Developer.md`「表示の決まり方」の「表示順・priority」の表は、
  同じ `col_list()` の情報を別の切り口（利用者向けは落ちる順だけ、
  開発者向けは表示順＋実際の priority 番号＋各列の中身）で示しており、
  文字どおりの重複ではない。design.md の役割分担
  （User.md は「幅による省略」、Developer.md は「`col_list()` と
  `priority`」）にも沿っている。**直すべき水準の重複ではないと判断する
  が、2 つの表が近い内容を持つこと自体は事実として報告する。**
  ほかに、3 文書間で本文が丸ごと重なる箇所は見つからなかった。

## 6. リンクとパス

- **確認した・問題なし**: `README.md` → `docs/User.md`（存在）、
  `docs/Developer.md`（存在）、`docs/fig1.png`（存在）。
  `docs/User.md` → `../README.md`（存在、相対パスの向きも正しい）。
  `docs/Developer.md` → `User.md`（存在、同じ `docs/` 内なので相対パスで正しい）。

## 見つけたこと（深刻度別）

**直すべき**: 無し。

**直した方がよい**: 無し。

**好み**: 上記「重複について」の 1 点のみ（表の内容が近い）。
直す必要は無いと考えるが、判断は管理者に委ねる。

## 確かめられなかったこと・判断できないこと

- implementer 報告にある「README の見出しの書式（`== ` 接頭辞を
  外した）」は design.md にも TODO.md にも明記が無く、外すのが
  正しいかどうかは判断できない。implementer 自身も「判断が要る点」と
  書いている（未回答のまま残っている）。
- `docs/fig1.png` の画像内容が現在の画面表示と一致しているかは
  確認していない（TODO-015 の方針どおり、新規スクリーンショットは
  撮っていないため）。implementer も同様に未確認と報告している。
- `-c` に不正な色名を渡したときに `click.style()` が `TypeError` に
  なる点（CLI 側で弾いていない）は、implementer 報告にある既知の
  懸念のとおりで、今回の文書の正確性には影響しない（現在の挙動を
  正しく書いているため問題視していない）。
