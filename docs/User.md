# tmr の使い方

`tmr` の全オプションと操作方法。
インストールと概要は [README.md](../README.md) を見てください。


## == 起動

インストール済みなら `tmr`、リポジトリで直接動かすなら
`uv run tmr` で起動します。以下は `tmr` と書きます。

```
Usage: tmr [OPTIONS] COMMAND [ARGS]...

  Timer CLI.

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

`t` は `timer` の、`p` は `pomodoro` の別名です。


## == 単純タイマー: `tmr timer`

分を指定して 1 回だけ計ります。分は 1 以上の整数です。

```
Usage: tmr timer [OPTIONS] MINUTES

  Simple Timer.

Options:
  -t, --title TEXT                alarm title  [default: Timer]
  -c, --title-color, --color TEXT
                                  title color  [default: blue]
  --alarm-count INTEGER RANGE     alarm count  [default: 999; x>=0]
  --alarm-sec1, --s1 FLOAT RANGE  alarm sec1  [default: 0.5; 0<=x<=86400]
  --alarm-sec2, --s2 FLOAT RANGE  alarm sec2  [default: 1.5; 0<=x<=86400]
  --alarm-cmd, --cmd TEXT         alarm command (instead of beep)
  -V, -v, --version               Show the version and exit.
  -d, --debug                     debug flag
  -h, --help                      Show this message and exit.
```

使用例:

```bash
tmr timer 5                          # 5 分
tmr timer 3 -t "Tea" -c green        # タイトルを "Tea"、緑で表示
tmr timer 10 --alarm-count 3         # 満了時に 3 回だけ鳴らす
```

`-c` に指定できるのは `click` の色名です
（`black` `red` `green` `yellow` `blue` `magenta` `cyan` `white` と、
その `bright_` 付き）。


## == ポモドーロタイマー: `tmr pomodoro`

作業と休憩を順に繰り返します。

```
Usage: tmr pomodoro [OPTIONS]

  Pomodoro Timer.

Options:
  -w, --work-time FLOAT RANGE     working time  [default: 25.0; x>0]
  -b, --break-time FLOAT RANGE    break time  [default: 5.0; x>0]
  -l, --long-break-time FLOAT RANGE
                                  long break time  [default: 15.0; x>0]
  -c, --cycles INTEGER RANGE      cycles  [default: 4; x>=1]
  --alarm-cmd, --cmd TEXT         alarm command (instead of beep)
  -V, -v, --version               Show the version and exit.
  -d, --debug                     debug flag
  -h, --help                      Show this message and exit.
```

時間の単位は分で、小数も書けます。

```bash
tmr pomodoro                         # 25 / 5 / 15 分、4 サイクル
tmr pomodoro -w 50 -b 10 -c 2        # 作業 50 分、休憩 10 分、2 サイクル
tmr pomodoro -w 0.1 -b 0.1 -c 2      # 動作確認用（6 秒ずつ）
```

### === フェーズの進み方

`-c 4` なら、作業 4 回のうち最後の休憩だけが長い休憩になります。
フェーズ名は画面のタイトルとして出ます（`WORK:1/4`、`SHORT_BREAK:1/4`、
`LONG_BREAK:4/4`）。図は [README.md](../README.md) にあります。

- フェーズが満了すると、アラームが鳴ります。
  キーを押すと次のフェーズへ進みます。
- `[N]` / `[ENTER]` を押すと、満了を待たずに次のフェーズへ進みます。
- `[Q]` / `[ESC]` を押すと、ポモドーロ全体が終わります。
- サイクルは `[Q]` を押すまで**何巡でも続きます**。
  `-c` は「長い休憩までの作業回数」であって、全体の回数ではありません。


## == キー操作

動作中に `[?]` を押すと、次の一覧が出ます。

```
COMMAND LIST
  [P], [SPACE]                            : Pause timer.
  [←], [Ctrl]+[B], [H], [-], [BACKSPACE]  : Backward 1 second.
  [→], [Ctrl]+[F], [L], [+], [=]          : Forward 1 second.
  [↑], [Ctrl]+[P], [K]                    : Backward 10 seconds.
  [↓], [Ctrl]+[N], [J]                    : Forward 10 seconds.
  [Ctrl]+[L]                              : Clear terminal.
  [N], [ENTER]                            : Next.
  [Q], [ESCAPE]                           : Quit.
  [?]                                     : Help.
```

- **`[N]` / `[ENTER]`（Next）はポモドーロでだけ有効**です。
  `tmr timer` では一覧にも出ません。
- 早送り・巻き戻しは、設定時間の範囲を超えません
  （0 秒より前にも、設定時間より後にも進みません）。
- ポーズ中は経過時間が止まり、画面の項目が点滅します。


## == 画面の見方

1 行に次の項目が並びます。

```
┌────────────────────────────────────────────────────────────────────────┐
│ 2026-09-08 14:03:21 Timer 25m  42.0% 10m30s >>>>>>>|___________ 14m30s │
└────────────────────────────────────────────────────────────────────────┘
  │          │        │     │    │     │      │                   │
  │          │        │     │    │     │      │                   └ remain
  │          │        │     │    │     │      └ pbar
  │          │        │     │    │     └ elapsed
  │          │        │     │    └ rate
  │          │        │     └ limit
  │          │        └ title
  │          └ time
  └ date
```

| 項目 | 意味 |
|---|---|
| `date` | 今日の日付 |
| `time` | 現在時刻 |
| `title` | `-t` で指定したタイトル（太字。色は `-c` で指定）。ポモドーロではフェーズ名 |
| `limit` | 設定時間 |
| `state` | 状態（後述）。通常は空 |
| `rate` | 経過率 |
| `elapsed` | 経過時間 |
| `pbar` | プログレスバー。残った幅を全部使う |
| `remain` | 残り時間 |

- `state` は `title` と `limit` の間に入ります。ポーズ中は `[PAUSE]`、
  満了してアラームが鳴っている間は `[TIME UP]` が点滅します。
- プログレスバーの先頭の `|` `/` `-` `\` は、動作中であることを示す
  風車です。ポーズ中と満了後は止まります。
- 経過率に応じて色が変わります。**80% 以上で黄、95% 以上で赤**
  （それより前は白）。色が変わるのは `state` `rate` `elapsed`
  `pbar` `remain` です。


## == 端末の幅が狭いとき

全部が収まらないときは、重要でない項目から順に落として 1 行に収めます。
幅を変えたときの実際の表示です。

```
 70 │ 2026-09-08 14:03:21 Timer 25m  42.0% 10m30s >>>>>>>|___________ 14m30s
 50 │ 14:03:21 Timer 25m  42.0% 10m30s >>>|______ 14m30s
 40 │ Timer 25m  42.0% >>>>>>|_________ 14m30s
 30 │ Timer 25m >>>>|________ 14m30s
 25 │ Timer >>>>|_______ 14m30s
 15 │ Timer 14m30s
 10 │ 14m30s
```

落とす順は決まっていて、次のとおりです（左から先に落ちる）。

| 落ちる順 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| 項目 | `date` | `time` | `elapsed` | `rate` | `limit` | `pbar` | `state` | `title` | `remain` |

つまり、最後まで残るのは `remain`（残り時間）です。
それでも収まらない場合は `!?` とだけ点滅表示します。

端末の幅を変えると、次の更新（0.2 秒ごと）から新しい幅で表示し直します。


## == アラーム

タイマーが満了すると、ベル文字（`\a`）を鳴らします。
実際に音が出るかは端末の設定によります
（`--alarm-cmd` を指定すると、代わりに任意のコマンドを実行します。後述）。

- 何かキーを押すと止まります。押したキーが `[Q]` / `[ESC]` なら、
  ポモドーロはそこで終わります。
- 鳴っている間も、画面は更新され続けます。

ベルの鳴らし方は `tmr timer` でだけ指定できます
（`tmr pomodoro` には次の 3 つのオプションはありません）。

| オプション | 意味 | 既定 |
|---|---|---|
| `--alarm-count` | 繰り返す回数 | 999 |
| `--alarm-sec1`, `--s1` | 1 回目の後に待つ秒数 | 0.5 |
| `--alarm-sec2`, `--s2` | 2 回目の後に待つ秒数 | 1.5 |

1 回の繰り返しで 2 回鳴らし、それぞれの後に `--s1` 秒、`--s2` 秒
待ちます。

- `--alarm-count 0` で**鳴らさなくなります**。
- 秒数に `0` を指定すると、間を空けずに鳴らします。
  上限は 86400 秒（1 日）です。

```bash
tmr timer 5 --alarm-count 0          # 鳴らさない
tmr timer 5 --alarm-count 5 --s1 0.2 --s2 0.2
```


### === ベルの代わりにコマンドを実行する

`--alarm-cmd`（短縮形 `--cmd`）を指定すると、ベルの代わりに
そのコマンドを実行します。音声ファイルの再生やデスクトップ通知に
使えます。`tmr timer` と `tmr pomodoro` の両方で使えます。

```bash
tmr timer 5 --alarm-cmd "aplay ~/sound/alarm.wav"
tmr timer 5 --cmd "notify-send 'tmr' 'time up'"
tmr pomodoro --cmd "paplay /usr/share/sounds/freedesktop/stereo/bell.oga"
```

- **ベルは鳴らなくなります**（置き換えです）。
  `--alarm-count` などは効きません。
- コマンドは**満了時に 1 回だけ**実行します。
- コマンドが終わっても、**キーを押すまでアラームの状態が続きます**
  （ベルのときと同じで、ポモドーロは次のフェーズへ進みません）。
- **キーを押すと、まだ動いているコマンドも止めます。**
  長く鳴らすコマンド（`mpv` で曲を流すなど）を指定しても、
  `[Q]` や `[N]` はすぐ効きます。`Ctrl-C` で終わらせたときも同じで、
  コマンドは止まります。
- コマンドの画面出力は**画面に出さず、ログに回します**
  （表示が崩れないため）。`-d` を付けると、出力（長いときは先頭だけ）と
  終了コードがログに出ます。失敗（コマンドが無い、非ゼロ終了）は `-d` 無しでも
  警告として出ます。
- コマンドが見つからない、または失敗した場合も、そのまま続きます。
  ベルには戻りません。
- コマンドはキーボードを読めません（入力は空になります）。
  `mpv` や `less` のように打鍵を待つコマンドは向きません。
- ポモドーロでは、全フェーズで同じコマンドを使います
  （作業と休憩で分けることはできません）。
- 空文字・空白のみ（`--cmd ""`）はエラーになります（終了コード 2）。

次の書き方は避けてください。**変なコマンドを書くと、tmr の側では
どうにもできません。**

- **出力が大量に出るコマンド**（`yes`、`tail -f` など）。
  コマンドの出力はログに回すために貯めるので、**tmr がメモリ不足で
  落ちることがあります**。
- **`&` を付けてバックグラウンドにする書き方**（`aplay foo.wav &` など）。
  キーを押しても止められず、**そのコマンドが終わるまで tmr 自体が
  止まって見えます**（キーを押しても画面が変わらず、ポモドーロなら
  次のフェーズにも進みません）。tmr から見るとシェルは既に終わって
  いるので、止める相手が分からないためです。

**注意: 指定した文字列は、そのままシェルに渡ります**
（`subprocess.Popen(cmd, shell=True)`）。パイプやリダイレクトも
書けますが、その分、書き間違いがそのまま実行されます。**設定ファイル
（`~/.config/tmr/config.toml`）に書いた文字列も同じくシェルに渡る**ので、
自分で書いた内容だけを置いてください。


## == 設定ファイル

よく使う値を `~/.config/tmr/config.toml` に書いておけます
（`XDG_CONFIG_HOME` があればそちらの下）。

```toml
debug = true          # tmr 自身のオプション

[timer]
minutes = 5
title = "Work"
title-color = "green"

[pomodoro]
work-time = 25.0
break-time = 5.0
cycles = 4
alarm-cmd = "aplay ~/sound/alarm.wav"
```

- セクション名はサブコマンドの名前（別名の `t` / `p` ではなく
  `timer` / `pomodoro`）。`tmr t` で起動しても `[timer]` が効きます
- キーは長い方のオプション名から `--` を取ったもの。
  `title_color` のようにアンダースコアで書いても構いません
- `timer` の `minutes` は引数ですが、これも書けます。
  書いておくと `tmr timer` だけで起動できます
- 優先順位は **コマンドライン引数 > 設定ファイル > 既定値**
- ファイルが無ければ、何も言わずに既定値を使います。
  TOML が壊れている、または知らないセクション・キーがある場合は、
  エラーを出して終了します
