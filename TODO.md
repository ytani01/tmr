# TODO

**残っている項目: TODO-001、TODO-002。** これまでに決着させた項目はまだ無い。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-003` から。**

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

## TODO-002. ログの水準を、クラス・モジュールごとに変えられるようにする

- [ ] `mylog.py` に `getLogger()` と、名前ごとの水準を見る filter を実装する
- [ ] 各モジュールを `_log` 経由の呼び出しに置き換える
- [ ] 環境変数 `TMR_LOG` の解釈を実装する
- [ ] テストを足す
- [ ] `CLAUDE.md` の「ログ」の節を直す

現在、`loggerInit(debug)` が全体を DEBUG か INFO のどちらかにするだけで
（`mylog.py:43`）、各モジュールは loguru のグローバル `logger` を直接
呼んでいる。`BaseTimer` のデバッグ出力だけを見たい、といったことが
できない。

### やり方

sink は 1 つのままにして、その `filter` で名前ごとに水準を判定する。
名前は `logger.bind()` の `extra` に入れる。試作して動くことは確認した。

```python
def getLogger(name):
    return logger.bind(log_name=name)

def _make_filter(levels):
    def _f(record):
        name = record["extra"].get("log_name", record["name"])
        lv = levels.get(name, levels.get("", "INFO"))
        return record["level"].no >= logger.level(lv).no
    return _f

logger.add(out, level=0, filter=_make_filter(levels), format=LOG_FMT)
```

- 名前は自由な文字列。クラス名でも `main` でもよい
- `log_name` が無いレコードは**モジュール名にフォールバック**するので、
  素の `logger.debug()` が残っていても壊れない
- sink の `level=0` が要る。ここを空けないと filter より先に切られる
- `{file}:{line} {function}()` は正しいまま出る（`bind` は呼び出し位置に
  影響しない）

呼び出す側は、**モジュールの先頭に `_log` を 1 つ置く**。

```python
# base_timer.py
_log = getLogger("BaseTimer")

class BaseTimer:
    def main(self):
        _log.debug("...")     # 子から呼ばれても "BaseTimer" のまま
```

こうすると、そのコードが書かれたファイルの名前で出るので、**継承しても
親と子が分かれる**。差分は `logger.` → `_log.` の機械的な置換で、
`base_timer.py` に約 20 か所、`progress_bar.py` に 1 か所、
`__main__.py` に 5 か所（名前は `main`）。

1 モジュールに、ログを出すクラスが 2 つあると名前を共有してしまうが、
今の tmr には該当が無い。そうなったら `_log_foo = getLogger("Foo")` を
並べる。

`self._log = getLogger(type(self).__name__)` を `__init__` で作る形も
考えたが、**親のメソッドの中のログまで子の名前になる**ので採らない。
`__set_name__` で定義側のクラスを覚えるデスクリプタも試したが、
`self._log` の属性探索が最派生クラスから始まるため同じ結果になり、
使えなかった。名前は自由な文字列なので、実クラスで分けたいクラスが
出てきたら、そこだけこの形を混ぜられる。

### 水準の指定

環境変数 `TMR_LOG` を使う。

```
TMR_LOG=BaseTimer=DEBUG,main=INFO
```

`--debug` は今までどおり全体を DEBUG にし、`TMR_LOG` の個別指定が
それを上書きする。

**設定ファイルから指定する話は TODO-001 の範囲で、今回はやらない。**

### 決めること

- 知らない名前を書かれたときに、黙って無視するか警告するか
- `LOG_FMT` に名前を出すか。今は `{file}:{line} {function}()` が出ていて
  `base_timer.py` と `BaseTimer` は重複気味。名前を出して `{file}` を
  落とすほうが読みやすいかもしれない
- `TMR_LOG` に加えて CLI オプション（`--log-level BaseTimer=DEBUG` を
  複数回）も足すか

モデル・effort: **Sonnet / medium**。やり方は上で決まっており、残るのは
`mylog.py` の実装と機械的な置換、テストの追加。規模は小さいため、
サブエージェントは編成しない。

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

（まだ無し）

---

## 補足

`archives/` 直下にある `20260211-*.md` などは、この運用を始める前の
過去の記録。**今後は参照しない**（`archives/todo/` とは別物）。
