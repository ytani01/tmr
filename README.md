# tmr -- CLIタイマー、ポモドーロタイマー

ターミナル上で動作する、効率的でカスタマイズ可能なタイマーです。
単純なタイマー機能と、ポモドーロ・タイマー機能があります。

## == 特徴
- **TUIによる進捗表示**: プログレスバーで残り時間を視覚的に把握できます。
- **カスタマイズ可能**: 作業時間、休憩時間、サイクル数を自由に変更できます。

## == Usage

```bash
uv run tmr --help

Usage: tmr [OPTIONS] COMMAND [ARGS]...

  Cli.

Options:
  -V, -v, --version  Show the version and exit.
  -d, --debug        debug flag
  -h, --help         Show this message and exit.

Commands:
  p         Pomodoro Timer.
  pomodoro  Pomodoro Timer.
  t         Simple Timer.
  timer     Simple Timer.
```

### === timer

```bash
uv run tmr timer --help

Usage: tmr timer [OPTIONS]

  Simple Timer.

Options:
  -t, --setting-time FLOAT   setting time  [default: 3.0]
  -c, --alarm-count INTEGER  alarm count  [default: 999]
  --alarm-sec1, --s1 FLOAT   alarm sec1  [default: 0.5]
  --alarm-sec2, --s2 FLOAT   alarm sec2  [default: 1.5]
  -V, -v, --version          Show the version and exit.
  -d, --debug                debug flag
  -h, --help                 Show this message and exit.
```

### === pomorodo

```bash
uv run tmr pomorodo --help

Usage: tmr p [OPTIONS]

  Pomodoro Timer.

Options:
  -w, --work-time FLOAT        working time  [default: 25.0]
  -b, --break-time FLOAT       break time  [default: 5.0]
  -l, --long-break-time FLOAT  long break time  [default: 15.0]
  -c, --cycles INTEGER         cycles  [default: 4]
  -V, -v, --version            Show the version and exit.
  -d, --debug                  debug flag
  -h, --help                   Show this message and exit.
```

---
(c) 2026 Yoichi Tanibayashi
