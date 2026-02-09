# Implementation Plan: src/base_timer.py の単体テストを作る

#### Phase 1: テスト基盤の整備とモックの実装 [checkpoint: 84b292d]
- [x] Task: テストファイルと基本的なフィクスチャの作成 [a6fff61]
    - [ ] `tests/test_base_timer.py` を作成し、基本的なインポートとテストクラスをセットアップする
    - [ ] `blessed.Terminal` を安全にモック化し、実際の端末操作を発生させない仕組みを作る
    - [ ] `time.sleep` や時刻取得をパッチし、決定論的なテストが可能な環境を整える
- [x] Task: Conductor - User Manual Verification 'Phase 1: テスト基盤の整備とモックの実装' (Protocol in workflow.md) [84b292d]

#### Phase 2: タイマーのコアロジックのテスト [checkpoint: eaaa38b]
- [x] Task: 状態管理とライフサイクルのテスト [6019ad5]
    - [x] `BaseTimer` の初期化、開始、停止、一時停止、再開の状態遷移を検証するテストを書く
    - [x] 既存のコードがこれらのテストにパスすることを確認し、必要に応じて修正する
- [x] Task: 時間計算と操作のテスト [e93f7c0]
    - [x] 時間のカウントダウンが（モック化された時間軸で）正確に行われることを検証するテストを書く
    - [x] 時間の加算・減算（スキップ/バック）機能が正しく動作することを検証するテストを書く
- [x] Task: Conductor - User Manual Verification 'Phase 2: タイマーのコアロジックのテスト' (Protocol in workflow.md) [eaaa38b]

#### Phase 3: TUI およびレイアウト計算のテスト [checkpoint: 165fff8]
- [x] Task: `TimerCol` とレスポンシブ・レイアウトのテスト [ef1ed65]
    - [x] `TimerCol` クラスの計算ロジック（幅に応じた表示選択）を検証するテストを書く
    - [x] 仮想的なターミナル幅を変更し、レイアウトが期待通りに追従することを検証するテストを書く
- [x] Task: 描画パラメータの計算テスト [ef1ed65]
    - [x] `get_draw_params` 等の描画用データ生成ロジックが正しい値を返すことを検証するテストを書く
- [x] Task: Conductor - User Manual Verification 'Phase 3: TUI およびレイアウト計算のテスト' (Protocol in workflow.md) [165fff8]

#### Phase 4: 入力ハンドリングと堅牢性のテスト [checkpoint: 14e2b76]
- [x] Task: キーボードイベント処理のテスト [8efb2aa]
    - [x] 特定のキー入力が期待されるコマンド（一時停止、終了等）に正しくマップされることを検証するテストを書く
    - [x] イベントループ内での入力待ちとタイムアウト処理をシミュレートするテストを書く
- [x] Task: エッジケースと堅牢性のテスト [8da9a02]
    - [x] 極端に狭い画面幅や、未知のキー入力に対する挙動を検証するテストを書く
- [x] Task: Conductor - User Manual Verification 'Phase 4: 入力ハンドリングと堅牢性のテスト' (Protocol in workflow.md) [14e2b76]

#### Phase 5: 品質保証とカバレッジの確認
- [x] Task: 最終的なカバレッジ確認とリファクタリング [ab0b706]
    - [x] `pytest --cov=src/tmr/base_timer.py` を実行し、未通過の分岐がないか確認する
    - [x] カバレッジ 80% 未満の場合は、不足しているケースを追加する
    - [x] テストコード自体をリファクタリングし、可読性とメンテナンス性を向上させる
- [ ] Task: Conductor - User Manual Verification 'Phase 5: 品質保証とカバレッジの確認' (Protocol in workflow.md)
