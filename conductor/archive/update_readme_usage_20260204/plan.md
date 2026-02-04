# Implementation Plan: update_readme_usage

## Phase 1: 情報収集と準備
- [x] Task: ヘルプ出力の取得
    - [x] `uv run pomodorocli --help` を実行して最新のヘルプ出力を取得する
- [x] Task: 現状の README 確認
    - [x] 現在の `README.md` の内容を確認し、追記・修正箇所を特定する

## Phase 2: README.md の更新
- [x] Task: インストール手順の記述
    - [x] `Installation` セクションを追加し、`uv` を用いたインストール方法を記述
- [x] Task: 使い方（Usage）の記述
    - [x] `Usage` セクションを追加し、コマンド例とヘルプ出力を記述
- [x] Task: スクリーンショット/Visuals の記述
    - [x] TUI の様子を表す説明またはプレースホルダーを追加

## Phase 3: レビュー
- [x] Task: プレビュー確認
    - [x] マークダウンが正しくレンダリングされるか確認する
- [x] Task: リンター実行
    - [x] `mise run lint`
