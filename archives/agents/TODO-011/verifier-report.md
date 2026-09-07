# TODO-011 verifier-report

## 検証コマンドと結果

- `uv run pytest tests -q` → 成功。`74 passed in 0.60s`
- `uv run ruff format --line-length 78 --diff src tests` → 差分なし
  （`20 files already formatted`）、終了コード 0
- `uv run ruff check --extend-select I src tests` → `All checks passed!`、
  終了コード 0
- `uv run basedpyright src tests` → `0 errors, 0 warnings, 0 notes`、
  終了コード 0
- `uv run mypy src tests` → `Success: no issues found in 20 source files`、
  終了コード 0

すべて成功。落ちた箇所は無し。`mise run` は使っていない。

## 変更ファイルの確認

`git status` / `git diff HEAD` で見えるのは次の 2 点のみで、対象範囲と一致する。

- `docs/mylog.md` を削除（`git rm` 済み、staged）
- `src/tmr/mylog.py` の冒頭 docstring に表と説明を追加（unstaged）

指示に無いファイルの変更は無い。

## 完了条件の読み合わせ

1. **表の移設** — `mylog.py` の docstring（4〜24 行目）に
   「`getLogger` と `loggerInit` の役割の違い」の表がある。
   旧 `docs/mylog.md` の表では「すること」列の `loggerInit(debug)` 側に
   「``TMR_LOG`` の反映を含めて」という記述があったが、新しい表では
   単に「loguru 本体を設定する」となっており、`TMR_LOG` への言及は
   削られている。条件を満たす。

2. **`docs/mylog.md` の削除** — `git status` で `deleted: docs/mylog.md`
   が staged になっており、`git rm` 相当の状態。`docs/` 配下は
   `fig1.png` のみになっている。条件を満たす。

3. **有効な情報の残存確認** — 旧 `docs/mylog.md` の内容を新
   `mylog.py` docstring・`CLAUDE.md`「ログ」節と突き合わせた。

   - 表・基本の使い方・サンプルコード・`exmsg` の説明は、形を変えて
     `mylog.py` の docstring に残っている（サンプルは `Base`/`Child` の
     継承例に更新されており、`exmsg` は関数自身の docstring と
     サンプルコード内で説明されている）。
   - 「`self._log = getLogger(...)` にしない理由」（MRO で子クラスの
     定義が親のログを上書きしてしまう話）は `CLAUDE.md` の「ログ」節に
     既にある内容と重複しており、消えていない。
   - 「名前が重複するとき（`_log_foo` / `_log_bar` のように分ける）」の
     節は、新しい docstring にも `CLAUDE.md` にも見当たらない。
     ただし現行の命名規約はクラス本体の `__qualname__` を使うため
     （TODO-004）、モジュール内で手動で名前を選ぶ場面自体が無くなっており、
     この情報は現在の設計では当てはまらないと判断できる（このリポジトリの
     実装を見た限りの判断であり、意図的に「使われなくなった情報」として
     省いたのか、単純な見落としかは、実装した本人に確認しないと分からない）。
   - 「関連」節（`archives/todo/TODO-002...md` と `mylog.py` 自身へのリンク）
     は、ファイル自身へのリンクなので省いて問題ない。
   - TODO.md の「現に古い記述」の表に挙がっている 6 項目
     （`TMR_LOG` の節、`_registered_names`、警告、フォールバック、
     モジュール先頭の `_log = getLogger("MyModule")`、
     `__main__.py`/`BaseTimer` の例）は、いずれも新しい docstring に
     残っていないことを確認した。

4. **実装との整合性** — `getLogger` / `setLevel` / `loggerInit` /
   `_levels` の実装（`src/tmr/mylog.py` 64〜141 行目）を読んだ限り、
   docstring の記述と矛盾は見当たらなかった。特に「`loggerInit()` を
   呼んでも名前ごとの水準は上書きされない」という記述は、
   `loggerInit()` が `_levels[""]` だけを書き換え、他のキーには
   触れないという実装（135 行目）と一致する。`CLAUDE.md` の
   「ログ」節とも矛盾しない。

5. **リンクの残存確認** — `grep -rn "mylog.md"` を `archives/` を除いて
   実行したところ、`TODO.md` の TODO-011 の項目名・本文中の言及
   （タスクの説明として `docs/mylog.md` という語を使っているだけで、
   リンクではない）以外にヒットしなかった。`README.md`・`CLAUDE.md`・
   `src/`・`tests/` のいずれにも `docs/mylog.md` へのリンクは残って
   いない。条件を満たす。

## 判断できないこと・残っている点

- TODO-011 のチェックリスト 3 項目目「`docs/` に `fig1.png` だけが
  残ることについて `CLAUDE.md` か `README.md` に記述が要るか見る」は
  未対応（`TODO.md` でも未チェックのまま）。今回の diff の対象範囲
  （`mylog.py` の docstring 追加と `docs/mylog.md` の削除）には
  含まれていないため、実施しなかったこと自体は指示違反ではないが、
  TODO-011 を完了扱いにするなら、この項目をやるか「不要」と決めるかを
  別途決める必要がある。
- 「名前が重複するとき」の情報を意図的に省いたのか、単なる漏れかは、
  実装した担当に確認しないと判断できない（上記 3 参照）。
