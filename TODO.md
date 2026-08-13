# TODO

**残っている項目: TODO-001, TODO-003。** これまでに 1 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-004` から。**

---

## TODO-001. 設定ファイル（`~/.tmr.toml`）から既定値を読む

- [ ] 読み込む項目と TOML の書き方を決める
- [ ] 読み込みを実装する
- [ ] テストを足す
- [ ] `README.md` と `CLAUDE.md` を直す

現在、時間・色などはすべてコマンドライン引数で毎回渡している。
よく使う値を `~/.tmr.toml` に書いておけるようにする。

決めること:

- **対象にする項目。** `timer` / `pomodoro` それぞれの時間、`--title`、
  `--title-color` あたりが候補。全オプションを対象にするかは要検討
- **優先順位。** コマンドライン引数 > 設定ファイル > コードの既定値、を
  想定。`click` の `default_map`（`Context.default_map`）を使えば
  引数の解釈に手を入れずに済むはずなので、まずこれを調べる
- **ファイルが無いとき・壊れているとき**の扱い（黙って既定値か、警告か）
- 置き場所を `~/.tmr.toml` にするか `~/.config/tmr/` にするか

モデル・effort: **Opus / medium**。
`click` の設定注入の仕組みを調べる必要があり、優先順位の設計も要る。
触るのは `__main__.py` と新しい読み込みモジュール、テストが中心で
規模は小さいため、サブエージェントは編成しない。

---

## TODO-003. ログの水準を、クラスごとに指定できるようにする

- [ ] `mylog.py` を書き直す（`TMR_LOG` の廃止、`setLevel()` の追加、
      `getLogger()` の `level` 引数）
- [ ] 各モジュールの `_log` を、クラス本体の `__log` に移す
- [ ] テストを直す
- [ ] `CLAUDE.md` のログの節を直す

現在、名前ごとの水準は環境変数 `TMR_LOG` からしか指定できない
（TODO-002）。**実行時に環境変数で切り替える用途は無く**、コードを
編集すれば足りる。一方、同じファイルにある複数のクラスや、親子
（継承）を別々の水準にしたい。これが必須。

### 使い方

```python
class BaseTimer:
    __log = getLogger("BaseTimer", "DEBUG")   # クラス本体に置く

    def pause(self):
        self.__log.debug("t_start をずらす")
```

- 水準を決めるのは、普段はクラス本体の `getLogger(name, level)`。
  テストや実行中など**外から**変えるときだけ `setLevel(name, level)`。
  `getLogger()` の `level` は `setLevel()` を呼ぶだけで、中身は同じ
- **`__log`（アンダースコア 2 つ）にする。** 名前修飾で
  `self._BaseTimer__log` に解決されるので、子クラスのインスタンスから
  親のメソッドを呼んでも親の名前で出る。`_log`（1 つ）だと MRO で子の
  定義が勝ち、親のログが子の水準で出てしまう
- クラスの無いモジュール（`__main__.py` の `main`）は、今までどおり
  モジュール先頭に `_log = getLogger("main")` でよい
- **`__init__` の中で `self.__log = ...` はしない。** 親子は分かれるが、
  `super().__init__()` を呼び忘れると親のメソッドが `AttributeError` で
  落ちる。`classmethod` から使えない、インスタンスを 1 つも作らないと
  水準が効かない、という問題もある

### `mylog.py` の形

```python
_levels: dict[str, int] = {"": 0}          # 水準は数値で持つ

def setLevel(name: str, level: str) -> None:
    _levels[name] = logger.level(level).no  # 知らない水準名はここで ValueError

def getLogger(name: str, level: str | None = None):
    if level is not None:
        setLevel(name, level)
    return logger.bind(log_name=name)

def _filter(record) -> bool:
    name = record["extra"].get("log_name", "")
    return record["level"].no >= _levels.get(name, _levels[""])

def loggerInit(debug: bool = False, out: TextIO = sys.stderr) -> None:
    logger.remove()
    _levels[""] = logger.level(logLevel(debug)).no
    logger.add(out, level=0, filter=_filter, format=LOG_FMT)
```

消えるもの: `TMR_LOG` / `_parse_tmr_log()` / `_registered_names` /
`_make_filter()` /「知らない名前です」の warning / 優先順位の設計。
113 行 → 45 行程度。`getLogger()` が import 時に書いた指定は、後から
`loggerInit()` が `_levels[""]` を入れ直しても消えないので、呼ぶ順を
気にしなくてよい。

### 決めること

- `TMR_LOG` は TODO-002 で入れたもの。廃止したら
  `archives/todo/TODO-002. ….md` に「TODO-003 で廃止した」と追記する

触るのは `src/tmr/mylog.py` / `base_timer.py` / `progress_bar.py` /
`__main__.py`、`tests/test_mylog.py`、`CLAUDE.md`。
モデル・effort: **Sonnet / medium**。変更は小さく、設計はここで
決まっているため、サブエージェントは編成しない。

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-002.** ログの水準を、クラス・モジュールごとに変えられるようにする](archives/todo/TODO-002.%20ログの水準を、クラス・モジュールごとに変えられるようにする.md)

---

## 補足

`archives/` 直下にある `20260211-*.md` などは、この運用を始める前の
過去の記録。**今後は参照しない**（`archives/todo/` とは別物）。
