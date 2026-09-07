# TODO

**残っている項目: TODO-007。** これまでに 6 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-008` から。**

---

## TODO-007. テストコードの後始末（mypy のエラーと残骸テスト）

|        | main                     | 担当     |
|--------|--------------------------|----------|
| 見込み | Opus 5 / effort high     | verifier |

- [ ] `tests/test_base_timer.py` の `__str__` 直接代入を直し、mypy を通す
- [ ] `tests/test_dummy.py` を削除する

`mise run lint` は mypy まで含むが、いま 2 件のエラーで止まっている。

```
tests/test_base_timer.py:195: error: Cannot assign to a method  [method-assign]
tests/test_base_timer.py:226: error: Cannot assign to a method  [method-assign]
```

どちらも `mock_key.__str__ = MagicMock(return_value=...)` の行。しかも
194 行目のコメントは「Use setattr to avoid lint errors with static
analyzers」と書いてあるのに直接代入しており、**コメントと実装が
食い違っている**。コメントどおり `setattr()` に戻せば両方そろう。
`# type: ignore[method-assign]` で黙らせる手もあるが、コメントとの
食い違いが残るので採らない。

`tests/test_dummy.py` は `print("Hello")` するだけで何も検証していない。
`git log` を見ると README 更新のついでに入ったきり触られていない。
残しておくとテスト件数が実態より多く見える。

完了条件は **`uv run mypy src tests` がエラー 0** で、`uv run pytest tests`
が通ること（削除した 1 件を除いて件数が減るのは想定どおり）。

挙動も分岐も変わらないので reviewer は付けず、確認は verifier に分ける。

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-006.** `CLAUDE.md` を `~/.claude/CLAUDE.md` の規約に合わせて整理する](archives/todo/TODO-006.%20CLAUDE.md%20を%20~-.claude-CLAUDE.md%20の規約に合わせて整理する.md)
- [**TODO-005.** `mylog.setLevel()` で変えた水準を既定に戻す API を足す](archives/todo/TODO-005.%20mylog.setLevel()%20で変えた水準を既定に戻す%20API%20を足す.md)
- [**TODO-004.** `getLogger()` の名前を `__qualname__` から取る](archives/todo/TODO-004.%20getLogger()%20の名前を%20__qualname__%20から取る.md)
- [**TODO-003.** ログの水準を、クラスごとに指定できるようにする](archives/todo/TODO-003.%20ログの水準を、クラスごとに指定できるようにする.md)
- [**TODO-002.** ログの水準を、クラス・モジュールごとに変えられるようにする](archives/todo/TODO-002.%20ログの水準を、クラス・モジュールごとに変えられるようにする.md)
- [**TODO-001.** 設定ファイル（`~/.config/tmr/config.toml`）から既定値を読む](archives/todo/TODO-001.%20設定ファイル（~-.config-tmr-config.toml）から既定値を読む.md)

---

## 補足

`archives/` 直下にある `20260211-*.md` などは、この運用を始める前の
過去の記録。**今後は参照しない**（`archives/todo/` とは別物）。
