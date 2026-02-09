# Task Completion Workflow

タスクを完了し、変更をコミットする前に以下のステップを必ず実行してください。

1. **静的解析とフォーマット:**
   ```bash
   mise run lint
   ```
   これには `ruff format`, `ruff check`, `basedpyright`, `mypy` が含まれます。

2. **テスト実行:**
   ```bash
   mise run test
   ```
   既存のテストがパスすることを確認し、新機能やバグ修正に対するテストを `tests/` に追加してください。

3. **ビルド確認 (任意):**
   ```bash
   mise run build
   ```
   配布可能な形式でビルドできるか確認します。

4. **Git コミット:**
   - 変更内容を `git status`, `git diff` で確認する。
   - `git add` で変更をステージングする。
   - `git log` で過去のコミットメッセージのスタイルを確認し、それに合わせたメッセージでコミットする。
