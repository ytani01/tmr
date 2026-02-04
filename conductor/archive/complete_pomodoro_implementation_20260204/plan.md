# Implementation Plan: complete_pomodoro_implementation

## Phase 1: 環境整備と基礎設計
- [ ] Task: 依存関係の追加
    - [x] `rich` を依存関係に追加 (`uv add rich`)
- [ ] Task: `App` クラスのリファクタリング
    - [x] 残り時間や現在のステータスを保持するように内部状態を整理

## Phase 2: タイマーロジックの実装 (TDD)
- [ ] Task: ユニットテストの作成
    - [x] `tests/test_app.py` を作成し、セッション遷移と時間計算のテストを記述
- [ ] Task: カウントダウンロジックの実装
    - [x] `App.cycle` 内で 1 秒刻みの正確なカウントダウンを実装
    - [x] テストがパスすることを確認 (`mise run test`)

## Phase 3: `rich` による TUI 実装
- [ ] Task: リアルタイム表示の導入
    - [x] `rich.live` を使用した表示ループの実装
- [x] Task: コンポーネントの構築
    - [x] プログレスバー、サイクル情報、ステータスラベルの配置
- [x] Task: カラーテーマの適用
    - [x] 状態（作業/休憩）に応じた色の切り替えロジックの追加

## Phase 4: 通知とユーザー確認
- [ ] Task: デスクトップ通知の実装
    - [x] OS 標準の通知コマンド（`notify-send` 等）の呼び出し処理を追加
- [x] Task: インターバル間のユーザー確認
    - [x] セッション終了時に入力を待機する処理の実装

## Phase 5: 仕上げと品質確認
- [ ] Task: リンターと型チェックの実行
    - [x] `mise run lint` を実行し、Ruff/Mypy の指摘を修正
- [x] Task: 最終動作確認
    - [x] 実際のポモドーロサイクルが意図通りに回るか手動でテスト
