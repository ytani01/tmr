# TODO-007. テストコードの後始末（mypy のエラーと残骸テスト）

|        | main                 | 担当     |
|--------|----------------------|----------|
| 見込み | Opus 5 / effort high | verifier |
| 実施   | Opus 5 / effort high | verifier |

| 担当     | モデル      | effort | output | cache_creation | 料金の割合 |
|----------|-------------|--------|--------|----------------|-----------|
| main     | Opus 5      | high   | 3,413  | 8,793          | 91%       |
| verifier | Haiku 4.5   | 記載なし | 2,031 | 22,631         | 9%        |
| 合計     |             |        | 5,444  | 31,424         | 概算 $0.7 |

- verifier は定義（`~/.claude/agents/verifier.md`）のモデルが haiku。
  上書きしていない
- verifier の定義には `effort` の行が無い（Haiku は effort に対応しない）

## きっかけ

`/doctor` でセットアップを点検したついでにリポジトリ全体を見たところ、
テストは 68 件すべて通り ruff と basedpyright もエラー 0 なのに、
**mypy だけが 2 件のエラーで止まっていた**。

```
tests/test_base_timer.py:195: error: Cannot assign to a method  [method-assign]
tests/test_base_timer.py:226: error: Cannot assign to a method  [method-assign]
```

`mise run lint` は mypy まで含むので、lint が最後まで緑にならない状態が
定着していた。こうなると、次に本物のエラーが出ても気付きにくい。

どちらも `mock_key.__str__ = MagicMock(return_value=...)` の行だが、
194 行目のコメントは

```python
# Use setattr to avoid lint errors with static analyzers
```

となっており、**`setattr` を使うと書いてあるのに直接代入していた**。
おそらく当初は `setattr` で書いていて、あとで戻されたまま放置された。

同時に、`tests/test_dummy.py` が `print("Hello")` するだけで何も検証して
おらず、`git log` を見ると README 更新のついでに入ったきり触られていない
のも見つかった。残しておくとテスト件数が実態より多く見える。

## やったこと

- `tests/test_base_timer.py` の 2 箇所を `setattr()` に変えた。
  コメントどおりの形になり、コメントと実装の食い違いも解消した
  - 195 行目 `setattr(mock_key, "__str__", MagicMock(return_value="p"))`
  - 226 行目 `setattr(mock_key, "__str__", MagicMock(return_value="\x01"))`
    （行末にあった `# Some control char` は行長 78 に収まらなくなったので
    前の行へ移した）
- `tests/test_dummy.py` を削除した

`# type: ignore[method-assign]` で黙らせる手もあったが、コメントとの
食い違いが残るので採らなかった。

## 確かめたこと

確認は verifier に分けた（報告は
`archives/agents/TODO-007/verifier-report.md`）。

| 確認 | 結果 |
|------|------|
| `uv run mypy src tests` | エラー 0（17 files） |
| `uv run pytest tests` | 67 件すべて通過 |
| `uv run ruff format --check --line-length 78 src tests` | already formatted |
| `uv run ruff check --extend-select I src tests` | All checks passed |
| `uv run basedpyright src tests` | 0 errors, 0 warnings |

件数が 68 → 67 に減ったのは削除した `test_dummy` の分で、想定どおり。
`setattr()` に変えてもテストが検証している内容（`get_key_name()` が
`"P"` と `"\x01"` を返すこと）は変わっていないことも確かめた。

`mise run test` / `mise run lint` は `upgradeproject` を巻き込んで
`uv.lock` を消すので使っていない。

## 分担の振り返り

- **verifier が見つけたもの: 無し。** 5 つの検証コマンドすべてで main の
  実行結果を再現し、差分が 2 ファイルに収まっていること、コメントと実装が
  一致したこと、テストの検証内容が骨抜きになっていないことを確認した。
  指摘はゼロだった
- **見込みと食い違わなかった。** 立てたときの見込み（main ＋ verifier）
  のまま実施した。挙動も分岐も変わらないので reviewer は付けず、
  それで困らなかった
- **次に同じ規模（テストコードの型注釈の手直し＋ファイル削除、
  完了条件がコマンド 1 つの終了状態で決まるもの）をやるなら、
  verifier だけを分ける今回の形をそのまま使う。**
  ただし verifier の料金の割合は 9%（$0.1）で、main が 91% を占めた。
  main 側の消費は会話の長さで決まっており、確認を分けたことによる
  上乗せは小さい。**削るなら verifier ではなく、main が確認コマンドを
  自分でも一通り流している分**（実装直後に 5 コマンド、verifier が
  同じものを再実行）。次は main 側は完了条件の mypy と pytest だけに留め、
  ruff と basedpyright は verifier に任せてよい
