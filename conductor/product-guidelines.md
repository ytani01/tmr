# Product Guidelines: tmr

## UX/UI Design Principles
- **Minimalism**: 必要な情報（残り時間、現在のサイクル、ステータス）のみをシンプルに表示する。
- **Responsiveness**: プログレスバーは滑らかに更新され、ユーザーの入力（中断など）に即座に反応する。
- **Terminal Integration**: 標準的なターミナルカラースキームを尊重し、特定の環境に依存しすぎない色使いにする。

## Implementation Guidelines
- **TUI (Text User Interface)**: 動的な表示には `rich` などのライブラリの採用を検討する（現在は標準出力ベース）。
- **Non-blocking**: タイマーが動作している間も、シグナル処理やユーザー入力を受け付けられるように設計する。
- **Configurability**: コードを直接変更しなくても、CLIオプションや（将来的に）設定ファイルで挙動を変更できるようにする。

## Error Handling
- 無効な時間設定が入力された場合は、適切なエラーメッセージを表示して終了する。
- `KeyboardInterrupt` (Ctrl+C) を適切にキャッチし、クリーンアップ（終了メッセージの表示など）を行ってから終了する。
