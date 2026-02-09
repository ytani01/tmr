# Product Guidelines - tmr

## Communication Style
- **Professional & Technical**: ユーザーに対しては、簡潔で正確な情報提供を旨とします。
- **Technical Accuracy**: 数値、状態遷移、エラーメッセージは技術的に正確であり、曖昧さを排除します。
- **Logging**: `loguru` を活用し、DEBUG, INFO, ERROR のレベルを適切に使い分けます。主要な処理ログは標準エラー出力（stderr）に集約し、標準出力（stdout）は TUI 描画に専念させます。

## Visual Identity & UI
- **Minimalist Detail**: 清潔なレイアウトを維持しつつ、進捗率、残り時間、サイクル数などの詳細情報を整理して表示します。
- **Color-Coded Status**: 色を状態の識別に活用します。
    - 作業中 (WORK): Cyan
    - 短い休憩 (SHORT_BREAK): Yellow
    - 長い休憩 (LONG_BREAK): Red
    - アラーム/警告: 特定の色（赤の反転など）
- **Responsive Logic (Priority-based)**: ターミナルのリサイズに対し、優先順位の低い要素（タイトル、補助テキスト等）から段階的に省略し、情報の有用性を最大化します。

## Documentation
- **Comprehensiveness**: ヘルプやドキュメントは、すべてのサブコマンド、オプション、キーバインドの仕様を網羅的に記述します。
- **Predictability**: ユーザーがドキュメントを読むことで、すべての動作と設定項目を正確に把握できるようにします。

## Error Handling
- **Structured Exit**: 終了コードを適切に使用し、他の CLI ツールやスクリプトからの呼び出しにおいて予測可能な動作を提供します。
- **Clear Messages**: エラー発生時は、原因が特定しやすい具体的なメッセージを表示します。
