# Tech Stack - tmr

## Core Language & Runtime
- **Python 3.13+**: モダンな Python 機能（型ヒント、f-strings 等）と最新のパフォーマンス改善を活用します。

## Project & Dependency Management
- **uv**: 非常に高速な Rust 製の Python パッケージマネージャー。プロジェクトの仮想環境管理、依存関係の解決、ロックファイルの管理に使用します。
- **mise**: 開発環境のツール管理（Python バージョン等）およびタスク（ビルド、テスト、リンター実行）の自動化に使用します。

## Application Frameworks
- **click**: 直感的で拡張性の高い CLI コマンドおよびオプションの構築に使用します。
- **blessed**: ターミナルの画面制御、色設定、キー入力のキャプチャ、レスポンシブな UI 描画を実現するためのバックエンド。

## Reliability & Quality
- **ruff**: 超高速な Python リンターおよびコードフォーマッター。プロジェクトのコーディング規約を強制します。
- **mypy & basedpyright**: 二つの静的型チェックツールを併用し、型の安全性とコードの品質を担保します。
- **py.typed**: `py.typed` マーカーを含めることで、ライブラリとしての利用時や静的解析ツールによる正確な型チェックをサポートします。
- **pytest**: ユニットテストおよび統合テストの実行に使用します。

## Infrastructure & Logging
- **loguru**: 構造化されたロギングを簡単に実現するためのライブラリ。
- **hatchling**: プロジェクトのビルドバックエンドとして使用します。
