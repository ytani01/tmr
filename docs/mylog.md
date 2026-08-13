# ログの使い方（`tmr/mylog.py`）

`tmr` は `loguru` のグローバル `logger` を使う。そのままだと
出力の水準（DEBUG / INFO）は全体で 1 つしか選べないため、
`mylog.py` はモジュール・クラスごとに名前を付けて、名前ごとに
水準を変えられるようにしている。

## `getLogger` と `loggerInit` の役割の違い

この 2 つは**別の場所で・別の目的で**呼ぶ。混同しやすいので先に整理する。

| | `getLogger(name)` | `loggerInit(debug)` |
|---|---|---|
| 呼ぶ場所 | 各モジュールの**先頭**（import 時に 1 回） | 各 **CLI コマンドの先頭**（実行時に 1 回） |
| 呼ぶ回数 | モジュールごとに 1 回 | プロセスごとに 1 回 |
| すること | ログの出どころに**名前タグを付ける**だけ | 出力先・水準・`TMR_LOG` の反映を含めて**loguru 本体を設定する** |
| 何も呼ばなかったら | `_log` が作れない（ログが出せない） | 名前ごとの水準指定が効かない（loguru が未設定なら出力先も無い） |

- `getLogger()` は「このログはどのモジュールのものか」を**宣言**するだけで、
  出力先や水準には一切関与しない。呼んだ時点ではまだ何も出力されない
- `loggerInit()` は逆に、**具体的な名前を一切知らない**。実際に出力する
  ための sink（出力先）を用意し、`TMR_LOG` を読んで「名前ごとの水準」の
  対応表を作り、それを filter として組み込むのがこの関数の仕事
- 順序としては、`getLogger()` は import 時（`loggerInit()` より前）に
  実行されるのが普通で、これが `TMR_LOG` の未知の名前チェック
  （後述）が成立する前提になっている

## 基本の使い方

**`getLogger()` と `loggerInit()` は両方使って初めて動く。**
片方だけではログが出ない、または名前ごとの水準指定が効かない
（詳しくは前節）。最小の構成はこうなる。

```python
# mymodule.py（ログを出す側）
from .mylog import getLogger

_log = getLogger("MyModule")   # (1) モジュールの先頭で名前を宣言


def do_something():
    _log.debug("start")        # "MyModule" という名前で出る
```

```python
# __main__.py（エントリーポイント）
from .mylog import loggerInit
from .mymodule import do_something


def main(debug: bool = False):
    loggerInit(debug)          # (2) 実行時に 1 度だけ、出力を用意する
    do_something()
```

- (1) `getLogger()` はモジュールを import した時点で実行され、
  「このログは "MyModule" というタグを持つ」と宣言するだけ。
  この時点ではまだどこにも出力されない
- (2) `loggerInit()` を呼んで初めて、実際に出力する sink が
  用意される。これを呼ばずに `_log.debug(...)` を書いても、
  loguru が未設定のままなので出力先が無い

`getLogger(name)` の `name` は自由な文字列。クラス名でも `main` でもよい。
モジュールの先頭で 1 度だけ呼び、以降はその `_log` を使う。

**メソッドの中で毎回 `getLogger()` を呼ばない。** 呼ぶたびに
`_registered_names` へ登録されるだけで害はないが、意味がない。

### なぜ `self._log = getLogger(...)` にしないか

`__init__` の中で `self._log = getLogger(type(self).__name__)` を
作る形も考えられるが、これだと**親クラスのメソッドの中のログまで、
実際には呼ばれていない子クラスの名前になる**（`self._log` の属性探索が
最派生クラスから始まるため）。モジュールの先頭に置く形なら、
**そのコードが書かれたファイルの名前で出る**ので、継承しても
親と子のログが混ざらない。

### 名前が重複するとき

1 モジュールに、ログを出すクラスが 2 つあると名前を共有してしまう。
そうなったら名前を分けて並べる。

```python
_log_foo = getLogger("Foo")
_log_bar = getLogger("Bar")
```

## tmr での実例

`tmr` では `__main__.py` の各 CLI コマンドの先頭で `loggerInit(debug)`
を 1 度だけ呼ぶ規約（`BaseTimer` をライブラリとして使う側も同じ）。
`__main__.py` 自身も `_log = getLogger("main")` を持っている点に注意
（`loggerInit()` を呼ぶ側も、ログを出す側でもある）。

```python
# __main__.py
from .mylog import getLogger, loggerInit

_log = getLogger("main")


@click.command()
def timer(debug, ...):
    loggerInit(debug)
    _log.debug("...")
```

`debug` は既定の水準を決める（`True` なら DEBUG、`False` なら INFO）。

## 水準を名前ごとに変える（`TMR_LOG`）

環境変数 `TMR_LOG` に `名前=水準` をカンマ区切りで書くと、
その名前の logger だけ水準を変えられる。`--debug` の指定より優先する。

```bash
TMR_LOG=BaseTimer=DEBUG,main=INFO uv run tmr timer 1
```

- 複数指定できる（カンマ区切り）
- 水準は `DEBUG` / `INFO` / `WARNING` など loguru の水準名
- `getLogger()` で一度も使われていない名前を書くと、起動時に
  warning が出る（打ち間違いに気づきやすくするため）
- `logger.debug(...)` のように名前を付けずに直接呼んだ場合は、
  呼び出し元の**モジュール名**（`base_timer` など）にフォールバックする

## 例外を 1 行にする（`exmsg`）

```python
from .mylog import exmsg

try:
    ...
except Exception as e:
    logger.error(exmsg(e))   # "ValueError: 使えない名前です" の形
```

## 関連

- 設計の背景・決めたことは
  [`archives/todo/TODO-002. ログの水準を、クラス・モジュールごとに変えられるようにする.md`](../archives/todo/TODO-002.%20ログの水準を、クラス・モジュールごとに変えられるようにする.md)
- 実装は [`src/tmr/mylog.py`](../src/tmr/mylog.py)
