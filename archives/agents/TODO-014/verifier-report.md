# TODO-014 確認報告（verifier）

## 1. ログが CLAUDE.md の「ログ」の節どおりか

`src/tmr/pomodoro.py` を確認した。

- `PomodoroTimer` クラス本体に `__log = getLogger(__qualname__)` があり、
  `__init__` / `run()` / `_run_timer()` は `self.__log.debug(...)` を
  使っている。`clock.py`（`__log = getLogger(__qualname__)` を
  クラス本体に置き、各メソッドで `self.__log.debug(...)`）と同じ書き方。
- クラスの無い `phases()` はモジュール先頭の `_log = getLogger("pomodoro")`
  を使っている。`cli.py` の `_log = getLogger("main")` と同じパターン
  （モジュール名を渡す）。
- `PomodoroConfig.__post_init__` にはログを足していない
  （依頼どおり、例外のみ）。

書き方は `CLAUDE.md` の規約、`clock.py` の実例と一致している。問題なし。

## 2. 足したテストが点滅の仕様を実際に捕まえるか（わざと壊して確認）

`src/tmr/view.py` の `display()` 内、点滅を決める箇所（186〜189行目）を
1 か所ずつ壊し、`uv run pytest tests/test_view.py -k blink -q` を実行した。
確認後は必ず元に戻し、`git diff src/tmr/view.py` が空であることを確認した
（他の未コミット差分には触れていない）。

### 2-1. `pause_blink` の分岐を壊す

```python
# 変更前
if col.pause_blink and clock.is_paused:
    f_blink = True
# 変更後（壊した状態）
if col.pause_blink and False:
    f_blink = True
```

結果、`test_display_pause_blink` が落ちた:

```
    def test_display_pause_blink(view, clock, mock_click):
        ...
        clock.is_paused = True
        show(view, clock)
        calls = {
            c.args[0]: c.kwargs["blink"] for c in mock_click.style.call_args_list
        }
>       assert calls[view.col["rate"].value] is True
E       assert False is True

tests/test_view.py:206: AssertionError
1 failed, 1 passed, 14 deselected in 0.12s
```

### 2-2. `state` 列の `is_timeup` 分岐を壊す

```python
# 変更前
if col.name == "state" and clock.is_timeup:
    f_blink = True
# 変更後（壊した状態）
if col.name == "state" and False:
    f_blink = True
```

結果、`test_display_timeup_blink` が落ちた:

```
    def test_display_timeup_blink(view, clock, mock_click):
        ...
        show(view, clock, is_active=False, alarm_active=True)
        calls = {
            c.args[0]: c.kwargs["blink"] for c in mock_click.style.call_args_list
        }
>       assert calls[view.col["state"].value] is True
E       assert False is True

tests/test_view.py:223: AssertionError
1 failed, 1 passed, 14 deselected in 0.13s
```

いずれも壊した側のテストだけが落ち、もう一方は通った（それぞれ狙った分岐を
個別に検知している）。壊した後は `\cp` でバックアップから戻し、
`git diff src/tmr/view.py` が空（差分無し）であることを確認済み。

## 3. テストの書き方の穴（`click.style` 呼び出しを値でキーにした dict）

`test_display_pause_blink` / `test_display_timeup_blink` はどちらも
`{c.args[0]: c.kwargs["blink"] for c in ...call_args_list}` という
「表示文字列をキーにした辞書」を作っている。複数の列が同じ文字列に
なった場合、後から処理された列の `blink` が先の値を上書きし、
取り違えが起きる作りではある。

ただし `display()` は `if not col.use or not col.value: continue` で
**空文字列の列を `click.style` の呼び出し自体から除外している**
（186行目直前）ため、`state` 列が `""` になる場面（ポーズ無し・満了前）
では辞書に `state` のキーが入らず、値の存在チェックではなく
`view.col["state"].value == ""` の直接比較で確認している。これは
衝突を避けた妥当な書き方。

今回の 2 つのテストの具体的な値（`t_limit=60.0`, `elapsed=10.0` または
`60.0`、`term.width=200`）で実際に `click.style` に渡る文字列を
書き出すと、`date` / `time` / `title="Timer"` / `limit` / `rate` /
`elapsed` / `pbar`（モックで `"----------"`）/ `remain` / `state`
（該当時のみ `"[PAUSE]"` または `"[TIME UP]"`）がそれぞれ異なる文字列に
なっており、**今回のテストでは実際の衝突は起きていない**ことを 2 の
壊す・戻す作業を通じて確認した（辞書のキー数と呼び出し回数が一致し、
落ちた行も期待どおりの箇所だった）。

懸念として残るのは、**将来 `elapsed` や `remain` などの値が偶然
`rate` や `state` と同じ文字列になった場合、この書き方では気づけない**
という一般的な脆さ。列のインデックスや `TimerCol` インスタンスをキーに
する（例えば `call_args_list` の呼び出し順と `col_list()` の並びを
突き合わせる）方が頑丈だが、現状のテストの意図（「点滅するかどうか」を
1 列だけ見る）は満たしており、**今回のテストが誤って通る／落ちる実害は
確認できなかった**。直すかどうかは管理者の判断。

## 4. 既存のテストとの重複

- `test_display_pause_state` / `test_display_timeup_state` は
  `col["state"].value` の**文字列そのもの**（`"[PAUSE]"` /
  `"[TIME UP]"` / `""`）を確認している。
- 今回追加した `test_display_pause_blink` / `test_display_timeup_blink` は
  `click.style` に渡る `blink` kwarg（**点滅の有無**）を確認しており、
  対象が異なる。`pause_blink` の分岐（186〜187行目）は既存の state 系
  テストでは検証されておらず（2 の実験で確認済み）、役割は重複していない。

## 5. 検証コマンド

すべて成功。

```
uv run pytest tests
→ 150 passed

uv run ruff format --check --line-length 78 src tests
→ 24 files already formatted

uv run ruff check --extend-select I src tests
→ All checks passed!

uv run basedpyright src tests
→ 0 errors, 0 warnings, 0 notes

uv run mypy src tests
→ Success: no issues found in 24 source files
```

## 変更ファイルと範囲の確認

`git status` / `git diff` で確認した変更は
`src/tmr/pomodoro.py` と `tests/test_view.py` のみ
（依頼書に書かれた対象と一致）。`archives/agents/TODO-014/` は
未追跡の報告ファイル群で、コードの変更ではない。壊す実験で触った
`src/tmr/view.py` は作業後に差分無しへ戻っていることを確認済み。

## 残る懸念・判断が要る点

- 実装報告にある通り、依頼書は `click.secho(..., blink=True)` を
  想定していたが、実装（`view.py`）は `click.style()` を使っている。
  テストは実装に合わせて `click.style` を対象にしており、点滅の有無を
  捉える意図は満たしている。これは実装側の既存コードとテストの整合の
  問題であり、今回の TODO-014 の範囲内で問題ないと判断したが、依頼書の
  記述と実装が食い違っていた点は事実として報告する。
- 3 で述べた「値をキーにした dict」の脆さは、今回のテストでは実害が
  無いことを確認したが、一般的な書き方としては頑丈ではない。直すか
  どうかは管理者の判断が要る。
