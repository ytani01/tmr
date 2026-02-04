# Track Specification: update_readme_usage

## 1. Overview
`README.md` を更新し、ユーザーが `pomodorocli` をスムーズにインストールして使用できるようにする。特に、新しく実装されたTUI機能やオプションについて詳しく記述する。

## 2. Functional Requirements
- **Installation Section**:
    - `uv` を使用した推奨インストール手順を記載する。
    - 開発版としてのインストール方法も含める。
- **Usage Section**:
    - `pomodorocli --help` の出力を引用し、全オプションを網羅する。
    - 具体的なコマンド例（デフォルト設定、時間指定など）を提示する。
- **Visuals**:
    - TUI（Richによるプログレスバー）の様子を示すテキストベースの表現、またはスクリーンショットエリア（プレースホルダー）を設ける。

## 3. Non-Functional Requirements
- **Clarity**: 初心者でも迷わず実行できる明確な記述にする。
- **Accuracy**: 現在の実装（Clickオプション、Rich TUI）と完全に一致させる。

## 4. Acceptance Criteria
- `README.md` に以下のセクションが存在し、内容が正確であること：
    - Installation
    - Usage (with Examples)
- マークダウンのフォーマットが崩れていないこと。
