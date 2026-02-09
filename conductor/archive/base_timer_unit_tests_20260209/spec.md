# Specification: src/base_timer.py の単体テストを作る

## 1. Overview
`src/tmr/base_timer.py` に含まれる `BaseTimer` クラスおよび関連クラス（`TimerCol`, `TimerCmd` 等）に対して、堅牢かつ包括的な単体テストを作成します。`blessed` ライブラリによる TUI 描画や時間の経過処理を適切にモック化し、高速で決定論的なテスト環境を構築します。

## 2. Functional Requirements
### 2.1 Core Logic Testing
- `BaseTimer` の初期化、開始、停止、一時停止、再開のロジックを検証する。
- タイマーのカウントダウンが正確に行われることを確認する（時間のモック化を利用）。
- 時間の加算・減算機能（進める・戻る）の動作を検証する。

### 2.2 TUI Logic Testing
- `TimerCol` による動的なカラム計算ロジックを検証する。
- ターミナルサイズ変更時に、レイアウトが崩れずに適切に再計算されることを確認する。
- プログレスバー描画に必要なパラメータが正しく計算されているか確認する。

### 2.3 Input Handling Testing
- キーボード入力（一時停止、終了、スキップなど）に対するイベントハンドラが正しく動作することを検証する。
- 無効なキー入力が無視される、または適切に処理されることを確認する。

## 3. Non-Functional Requirements
- **Mocking**: `unittest.mock` や `freezegun` (または `time` モジュールのパッチ) を使用し、テスト実行時間を最小化する。実際の `sleep` は行わない。
- **Coverage**: `src/tmr/base_timer.py` のコードカバレッジ 80% 以上を目標とする。
- **Maintainability**: テストコードは可読性を重視し、将来的なリファクタリング時に仕様の防波堤となるように記述する。

## 4. Out of Scope
- `blessed` ライブラリ自体の機能テスト（ライブラリを信頼する）。
- OS 固有の挙動や、極端なエッジケース（メモリ不足など）のテスト。
