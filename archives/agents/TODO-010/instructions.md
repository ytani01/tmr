# TODO-010 implementer への依頼

`Timer` を分割し、引数をデータクラスにする。リポジトリは
`/home/ytani/work/tmr`、ブランチ `develop`。

**設計はこの文書で確定している。勝手に変えないこと。** 迷ったら実装を止めて
報告に書く。

## 目的

`src/tmr/timer.py`（516 行）に、時刻の計算・表示・キー操作・アラームが
すべて入っている。時刻と表示を別モジュールへ出し、`Timer` を
「メインループとキー操作・アラームだけの層」にする。

**挙動は変えない。** 画面に出る文字列、キー割り当て、`main()` の戻り値、
省略される項目の順番は今と同じであること。

## 1. `src/tmr/clock.py` — `TimerClock`

端末に依存しない時刻の管理。`Timer` から次を移す。

```python
class TimerClock:
    __log = getLogger(__qualname__)

    def __init__(self, t_limit: float): ...
    #   self.t_limit, self.t_start = 0.0, self.elapsed = 0.0,
    #   self.is_paused = False

    def start(self) -> None:        # t_start を現在時刻に、elapsed を 0 に
    def tick(self) -> None:         # メインループから毎周回呼ぶ
    def toggle_pause(self) -> None:
    def forward(self, sec: float = 1.0) -> None:
    def backward(self, sec: float = 1.0) -> None:

    @property
    def remain(self) -> float:      # max(t_limit - elapsed, 0)
    @property
    def rate(self) -> float:        # elapsed / t_limit * 100（%）
    @property
    def is_timeup(self) -> bool:    # elapsed >= t_limit
```

計算は現行の `Timer.main()` / `fn_forward()` / `fn_backward()` から
**式をそのまま移す**（早送り・巻き戻し・ポーズは `t_start` をずらして
表現する。`elapsed` を直接いじらない）。`rate` のゼロ除算も現行のままでよい
（`t_limit=0` は現行でも例外になる。ここで仕様を足さない）。

`Timer` 側には `t_start` / `t_elapsed` / `is_paused` を**残さない**
（`timer.clock.elapsed` のように参照する。2026-09-08 に利用者と決めた）。

## 2. `src/tmr/view.py` — `TimerCol` / `TimerTitle` / `TimerView`

### `TimerTitle`

```python
@dataclass(frozen=True)
class TimerTitle:
    text: str
    color: str = "white"
    width: int = 0   # 0 なら整形しない
```

`width` が正なら表示時に `f"{text:{width}s}"` で桁を揃える
（`PomodoroTimer` が持っていた `f"{tt:16s}"` の移し先）。

### `TimerCol`

**表示順と削除の優先順位を 1 箇所にまとめる**（この項目の眼目）。
現行は `col_list()` の挿入順（表示順）と `COL_PRIORITY`（削る順）の
二重管理になっている。`TimerCol` に `priority` を持たせ、**定義の並びが
表示順、`priority` の小さいものから削る**形にする。

```python
@dataclass
class TimerCol:
    name: str
    priority: int          # 小さいほど先に削られる
    value: str = ""
    color: str = "white"
    rate_color: bool = False
    bold: bool = False
    pause_blink: bool = False
    use: bool = True
```

現行の `COL_PRIORITY` は末尾から `pop` するので、削られる順は
date → time → elapsed → rate → limit → pbar → state → title → remain。
表示順は date, time, title, limit, state, rate, elapsed, pbar, remain。
**この 2 つが今と同じになるように `priority` を振る**（date=1 …
remain=9）。表示順の定義は 1 つのリスト（またはそれを返すメソッド）だけに
なること。

### `TimerView`

```python
class TimerView:
    __log = getLogger(__qualname__)

    def __init__(self, term, t_limit: float, title: TimerTitle): ...
    #   self.pbar = ProgressBar(t_limit) をここで作る

    def display(
        self, clock: TimerClock, *,
        is_active: bool, alarm_active: bool,
    ) -> None: ...
```

`Timer.display()` の中身をそのまま移す。`PERCENT_COLOR`、`PBAR_LEN_MIN`、
`STAT_STR_PAUSE`、`STAT_STR_TIMEUP` も `TimerView` へ移す。
`Terminal` は `Timer` が作って渡す（`term.cbreak()` / `inkey()` を
`Timer` が使うため）。`ProgressBar` は `TimerView` が作る。

## 3. `src/tmr/timer.py` — `Timer`

```python
@dataclass(frozen=True)
class AlarmParams:
    count: int
    sec1: float
    sec2: float


class Timer:
    DEF_TITLE = TimerTitle("Timer", "white")
    DEF_ALARM = AlarmParams(COUNT_MANY, DEF_SEC1, DEF_SEC2)

    def __init__(
        self,
        title: TimerTitle = DEF_TITLE,
        t_limit: float = DEF_LIMIT,
        alarm_params: AlarmParams = DEF_ALARM,
        enable_next: bool = False,
    ): ...
```

`Timer` に残るのは `main()`、`get_key_name()`、`cmd_list()`、`fn_*`、
`keys_str()`、`mk_cmd_str()`、`thr_alarm()`、`ring_alarm()`、`key_map`。

- `fn_pause` → `self.clock.toggle_pause()`
- `fn_forward` / `fn_backward` → `self.clock.forward(sec)` / `.backward(sec)`
- `main()` の時刻の計算 → `self.clock.start()` / `self.clock.tick()`
- 終了判定 → `self.clock.is_timeup`
- 表示 → `self.view.display(self.clock, is_active=..., alarm_active=...)`
- `thr_alarm` へ渡す引数は `AlarmParams` から展開する

`type AlarmParams = tuple[int, float, float]` の別名は消す。

## 4. `src/tmr/pomodoro.py`

フェーズの並びをジェネレータに分離する。

```python
def phases(config: PomodoroConfig) -> Iterator[tuple[TimerTitle, float]]:
    """フェーズの並びを、無限に返す。"""
```

`WORK` → `SHORT_BREAK`（最後の周回だけ `LONG_BREAK`）の順、色は
cyan / yellow / red、`width=16`。現行の `run()` の `while True` と同じく
サイクルを繰り返す。

```python
class PomodoroTimer:
    def run(self) -> bool:
        for title, sec in phases(self.config):
            if self._run_timer(title, sec):
                return True
        return False
```

`_run_timer(self, title: TimerTitle, seconds: float) -> bool` に変える
（`f"{tt:16s}"` の桁揃えは `TimerTitle.width` に移った）。

## 5. `src/tmr/cli.py`

`Timer((title, title_color), limit, (alarm_count, alarm_sec1, alarm_sec2))`
を新しいデータクラスに直す。**CLI のオプションは変えない**
（`README.md` の help 出力に手を入れる必要が無いこと）。

## 6. テスト

- `tests/test_clock.py`（新規）— `tmr.clock.time` をモックして、
  経過・ポーズ・早送り・巻き戻し・`remain` / `rate` / `is_timeup`
- `tests/test_view.py`（新規）— 幅が足りないときに削られる順、
  経過率による色、ポーズ中の表示、`TimerTitle.width` の桁揃え。
  `Terminal` はモックし、`term.width` には**数値**を入れる
- `tests/test_timer.py` — 新しい構成に合わせて直す。
  `timer.t_elapsed` などは `timer.clock.elapsed` に読み替える
- `tests/test_pomodoro.py` — `phases()` そのもののテストを足す
  （最初の 1 サイクル分の並び・色・秒数）

**既存のテストを消して減らさない。** 移し替えるのはよいが、
今あるケースが新しい構成のどこかで見られていること。

## 7. 文書

`CLAUDE.md` の「設計」節を新しい構成に直す。少なくとも次の 3 か所。

- 「`Timer` が本体」— `timer.py` にすべて入っている、という記述
- 「表示は 2 つのリストで決まる」— `col_list()` + `COL_PRIORITY` の
  二重管理の説明（1 箇所にまとまったので書き直す）
- 「テスト」節のモック先（`tmr.timer` の `Terminal` / `ProgressBar`）

`README.md` は CLI が変わらないので触らない。**利用者向けの文書に
TODO 番号を書かない。**

## 8. 検証

```bash
uv run pytest tests -q
uv run ruff format --line-length 78 src tests
uv run ruff check --fix --extend-select I src tests
uv run basedpyright src tests
uv run mypy src tests
```

**`mise run` は使わない**（`uv.lock` を作り直してしまう）。
行長は 78 文字。

手元での動作確認も 1 度やること。

```bash
uv run tmr timer 0.05
uv run tmr pomodoro -w 0.05 -b 0.05 -c 2
```

（すぐ鳴り終わるので、`q` で抜ける。端末が対話できないときは、
できなかったと報告に書く）

## 9. 報告

`archives/agents/TODO-010/implementer-report.md` に、変えたファイル、
設計から外れた点とその理由、検証の結果、残る懸念を書く。
返事は「終わったか・報告ファイルのパス・判断が要る点」を 5 行以内で。

**コミットはしない**（管理者がまとめて行う）。
