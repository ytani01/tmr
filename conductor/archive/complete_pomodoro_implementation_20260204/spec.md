# Track Specification: complete_pomodoro_implementation

## 1. Overview
未完成のポモドーロ・タイマーの実装を完了させ、実用的なCLIツールとして提供する。`rich` ライブラリを活用した視覚的なフィードバック（TUI）と、デスクトップ通知機能を備える。

## 2. Functional Requirements
- **TUI Implementation**:
    - `rich.progress` または `rich.live` を使用した動的なプログレスバーの表示。
    - 現在のサイクル数（例: 1/4）およびセッション種別の表示。
    - 状態（Work: 赤系 / Break: 緑系）に応じたカラーテーマの適用。
- **Timer Logic**:
    - 1秒刻みの正確なカウントダウン処理の実装。
    - 各セッション（Work, Break, Long Break）の適切な遷移。
- **Notifications**:
    - セッション終了時のデスクトップ通知（システムコマンドの呼び出し）。
    - 通知後のユーザーによる継続確認（キー入力待ち）。

## 3. Non-Functional Requirements
- **Resource Efficiency**: CPU使用率を抑えたループ処理（適切な `sleep`）。
- **Signal Handling**: `Ctrl+C` でのクリーンな終了。

## 4. Acceptance Criteria
- 指定した作業/休憩時間が正しくカウントダウンされ、プログレスバーに反映されること。
- セッション終了時に通知が飛び、ユーザーがキーを押すまで次のセッションに進まないこと。
- `rich` による表示が乱れず、ターミナル上で正しく更新されること。
