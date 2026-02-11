# Action Plan 2.4: ポモドーロロジックのクラス化 (Quit対応版)

`action-plan2.md` の「4. ポモドーロロジックのクラス化」について、`quit` コマンドによる全体終了を考慮した詳細設計です。

## 概要

`pomodoro` コマンドのロジックを `PomodoroCore` クラスに移動します。
`BaseTimer.main()` の戻り値（`True` = Quit）を適切にハンドリングし、どの段階でも `q` キー等で直ちにポモドーロ全体を終了できるようにします。

## 詳細設計

### 1. [NEW] src/tmr/pomodoro.py

`PomodoroCore` クラスを作成します。
`run()` メソッドは、ユーザによる中断（Quit）があった場合に `True` を返し、正常終了時（もしあれば）には `False` を返すように設計しますが、現状のポモドーロは無限ループ仕様なので、基本的には `True` (Quit) で戻るか、例外での脱出になります。

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

    def run(self) -> bool:
        """ポモドーロサイクルの実行
        
        Returns:
            bool: ユーザ中断(quit)があった場合は True、それ以外は False
        """
        while True:
            for i in range(self.config.cycles):
                # Work
                if self._run_timer("WORK", self.config.work_sec, "cyan"):
                    return True # Quit
                
                # Break
                if i < self.config.cycles - 1:
                    # Short Break
                    if self._run_timer("SHORT_BREAK", self.config.break_sec, "yellow"):
                        return True # Quit
                else:
                    # Long Break
                    if self._run_timer("LONG_BREAK", self.config.long_break_sec, "red"):
                        return True # Quit
            
            # forループが中断されずに完了した場合、whileループで次のサイクルへ
            # (現状の仕様通り、無限に繰り返す)

    def _run_timer(self, title_text: str, seconds: float, color: str) -> bool:
        """単発タイマーの実行
        
        Returns:
            bool: BaseTimer.main() の戻り値 (True=Quit)
        """
        timer = BaseTimer((title_text, color), seconds, enable_next=True)
        return timer.main()
```

### 2. [MODIFY] src/tmr/__main__.py

`pomodoro` コマンドの実装を `PomodoroCore` を使用するように変更します。
無限ループの制御などが `pomodoro.py` 側に移譲されるため、`__main__.py` は非常にシンプルになります。

```python
from .pomodoro import PomodoroCore, PomodoroConfig

# ... (options) ...
def pomodoro(ctx, work_time, break_time, long_break_time, cycles, debug):
    """Pomodoro Timer."""
    loggerInit(debug)
    # ... (logging) ...

    # 秒換算
    config = PomodoroConfig(
        work_sec=work_time * SEC_MIN,
        break_sec=break_time * SEC_MIN,
        long_break_sec=long_break_time * SEC_MIN,
        cycles=cycles
    )

    core = PomodoroCore(config)
    
    with TerminalContext():
        core.run()
```

## メリット

1. **可読性の向上**: ネストしたループ条件や `break/else/continue` の複雑な制御構文が、メソッド分割と `return` による早期脱出によって整理されます。
2. **Quit処理の統一**: `_run_timer` の戻り値をチェックして即座に `return True` することで、どのフェーズにいても確実に終了できます。
3. **テスト容易性**: `PomodoroCore` 単体でのインスタンス化が可能になり、`Mock` オブジェクトを使った状態遷移のテストが書きやすくなります。
