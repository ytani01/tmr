# Action Plan: src/tmr/

`code-review2.md`、`code-review1.md` での指摘に基づき、具体的な修正・改善案を提示します。

## 1. リファクタリング: 共通処理の切り出し

### 課題
`__main__.py` 内の `timer` コマンドと `pomodoro` コマンドの両方で、カーソル制御 (`ESQ_CSR_OFF` / `ESQ_CSR_ON`) と `KeyboardInterrupt` による終了処理が重複しており、保守性が低い状態です。

### 改善案: `TerminalContext` クラスの導入
コンテキストマネージャを使用して、カーソル制御と終了処理をカプセル化します。

#### [NEW] src/tmr/utils.py (提案)
```python
import click
from . import ESQ_CSR_OFF, ESQ_CSR_ON, ESQ_EL2

class TerminalContext:
    """端末のカーソル制御と終了処理を行うコンテキストマネージャ"""
    def __enter__(self):
        # カーソルを消す
        click.echo(ESQ_CSR_OFF, nl=False)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # 例外発生時も含め、必ずカーソルを表示に戻す
        click.echo(f"End.{ESQ_CSR_ON}")
        
        if exc_type is KeyboardInterrupt:
            # KeyboardInterrupt はここで処理し、スタックトレースを出さずに終了
            click.echo(f"{ESQ_EL2}\rAborted.", nl=False)
            return True # 例外を抑制
```

#### [MODIFY] src/tmr/__main__.py
```python
from .utils import TerminalContext

@click.command()
# ... (省略)
def timer(...):
    # ...
    limit = int(minutes * SEC_MIN)
    
    with TerminalContext():
        BaseTimer(
            ("Timer", "blue"), limit, (alarm_count, alarm_sec1, alarm_sec2)
        ).main()

# pomodoro も同様に with TerminalContext(): でラップ
```

---

## 2. テストの追加

### 課題
`__main__.py` のロジック、特に `pomodoro` コマンドの状態遷移や引数パースのテストが皆無（カバレッジ 0%）です。

### 改善案: `PomodoroTimer` ロジックの分離とテスト実施
`__main__.py` にあるロジックをクラスに切り出し、単体テストを可能にします。（後述の「4. ポモドーロロジックのクラス化」と連動）

#### [NEW] tests/test_pomodoro.py (提案)
まずは現状の `__main__.py` を外部から実行して動作を確認する結合テストを作成します。

```python
from click.testing import CliRunner
from tmr.__main__ import pomodoro

def test_pomodoro_args():
    runner = CliRunner()
    # 引数パースのテスト（実際にタイマーが動くと長くなるので、--help 等で確認するか、内部ロジックをモックする必要あり）
    result = runner.invoke(pomodoro, ['--help'])
    assert result.exit_code == 0
    assert "pomodoro" in result.output
    assert "--work-time" in result.output

# ロジック切り出し後は、PomodoroTimer クラスの単体テストを追加する
# def test_pomodoro_cycle():
#     p = PomodoroTimer(cycles=2, ...)
#     assert len(p.schedule) == 4 # Work, Break, Work, LongBreak
```

---

## 3. 型ヒントの修正

### 課題
`mypy` で検出される型エラー予備軍や、`typ`o が放置されています。

### 改善案: 具体的な型定義の適用

#### [MODIFY] src/tmr/base_timer.py

**typo の修正と型定義の強化:**
```python
# Before
# arlarm_params: tuple[int, float, float] = (...)  # typo

# After
AlarmParams = tuple[int, float, float] # 型エイリアス定義

class BaseTimer:
    def __init__(
        self,
        # ...
        alarm_params: AlarmParams = (COUNT_MANY, DEF_SEC1, DEF_SEC2), # typo修正
        # ...
    ):
        self.alarm_params = alarm_params
```

**`col_list` の戻り値型:**
```python
# Before
# def col_list(self) -> dict[str, TimerCol]:

# After (特段変更不要に見えるが、dictの中身が明示されているか確認)
# 既に dict[str, TimerCol] になっているのであればOK。もし単なる dict なら修正。
```

#### [MODIFY] src/tmr/__init__.py

**`__all__` の不足解消:**
```python
__all__ = [
    "__version__",
    "logger",
    "SEC_MIN",
    "MIN_HOUR",
    "ESC",
    "ESQ_CSR_ON",
    "ESQ_CSR_OFF",
    "ESQ_EL0",
    "ESQ_EL1",  # 追加
    "ESQ_EL2",  # 追加
]
```

---

## 4. ポモドーロロジックのクラス化

### 課題
`pomodoro` コマンドの実装が `while` ループと `for` ループのネストで複雑化しており、可読性が低く、拡張（例：一時停止機能の共有化など）が困難です。

### 改善案: `PomodoroCore` (仮) の作成
状態管理を行うクラスを作成し、`__main__.py` はそのクラスを使って実行するだけにします。

#### [NEW] src/tmr/pomodoro.py (提案)
```python
from dataclasses import dataclass
from .base_timer import BaseTimer

@dataclass
class PomodoroConfig:
    work_sec: float
    break_sec: float
    long_break_sec: float
    cycles: int

class PomodoroCore:
    def __init__(self, config: PomodoroConfig):
        self.config = config

    def run(self):
        """ポモドーロサイクルの実行"""
        while True: # 無限ループモードの場合
            for i in range(self.config.cycles):
                # Work
                self._run_timer("WORK", self.config.work_sec, "cyan")
                
                # Break
                if i < self.config.cycles - 1:
                    self._run_timer("SHORT_BREAK", self.config.break_sec, "yellow")
                else:
                    self._run_timer("LONG_BREAK", self.config.long_break_sec, "red")
    
    def _run_timer(self, title_text, seconds, color):
        timer = BaseTimer((title_text, color), seconds, enable_next=True)
        timer.main()
        # ここで終了コードなどを判定して break するロジックを入れる
```

#### [MODIFY] src/tmr/__main__.py
```python
from .pomodoro import PomodoroCore, PomodoroConfig

def pomodoro(ctx, work_time, ...):
    config = PomodoroConfig(...)
    core = PomodoroCore(config)
    with TerminalContext():
        core.run()
```
