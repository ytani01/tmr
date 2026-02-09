# Code Review - Round 1: src/tmr/

- [1. base_timer.py](#1-base_timerpy)
- [2. progress_bar.py](#2-progress_barpy)
- [3. click_utils.py](#3-click_utilspy)
- [4. mylog.py](#4-mylogpy)
- [5. __init__.py](#5-__init__py)
- [6. __main__.py](#6-__main__py)
- [7. tests/](#7-tests)
- [8. 全体的な設計・アーキテクチャ](#8-全体的な設計アーキテクチャ)

## 1. base_timer.py

### logic Correctness & Efficiency
- **Critical:** `ring_alarm` が `threading.Thread` を `daemon=True` で開始しているが、メインスレッドが終了した際のアラーム停止処理が不十分。`KeyboardInterrupt` 時のハンドリングはあるが、`tmr.main()` が終了した後のアラーム継続中にアプリケーションが終了するとスレッドが強制終了される。
- **High:** `display` メソッド内の `while all_len(col_disp) > self.term.width:` ループ。`col_disp.pop()` はリストの末尾（現在 `date`）を削除するが、優先度リスト `col_disp` の設計意図（`remain` が最高優先度）と合致しているか再考の余地あり。
- **Medium:** `get_key_name` 内で `in_key.name` が `None` の場合に空文字を返しているが、呼び出し元では `key_name in self.key_map` でチェックしているため、不整合はないが冗長な `if` 文が見られる。
- **Medium:** `col_list` が辞書を返しているが、順序に依存している（`**重要**: 表示順にすること`）。Python 3.7+ では辞書の順序は保持されるが、より明示的な順序管理や、`dataclass` でフィールド定義する方が堅牢。

### Type Safety
- **Medium:** `arlarm_params` ( typo: `alarm_params`) の型が `tuple` または `list` として扱われているが、要素数や型が固定されているため、`tuple[int, float, float]` のように詳細に定義すべき。
- **Medium:** `col_list` の戻り値型が `dict` となっているが、`dict[str, TimerCol]` とすべき。
- **Low:** `keys_str` の引数 `key_list` が `list[str]` となっているが、`List[str]` (from typing) と `list` が混在している。

### Suggestions
- **Refactoring:** `TimerCol` を `dataclass` にしているのは良いが、`display` 内での文字列生成ロジックが肥大化している。各 `TimerCol` が自身の文字列化（色付け含む）を担当するように責務を分散できる。
- **Improvement:** `ProgressBar` との統合。`BaseTimer` が `ProgressBar` を持っているが、`display` 内で `ProgressBar` の内部状態を操作（`self.col["pbar"].value = ...`）している。

## 2. progress_bar.py

### Logic Correctness & Efficiency
- **Medium:** `get_str` 内の `on_len` 計算。`round(rate * bar_len)` を使用しているが、100%に達する前にバーが満杯に見える可能性がある。`int(rate * bar_len)` の方が直感的かもしれない。
- **Medium:** `self.ch_head_i` の更新が `get_str` (Getter) の中で行われている。これは副作用であり、同じ値で複数回呼び出すと風車が回ってしまう。

### Type Safety
- **Medium:** `ProgressBar.display` の `bar_len` デフォルト値が `0` だが、`get_str` では `None` の場合に `self.bar_len` を使うようになっている。一貫性が必要。

## 3. click_utils.py

### Logic Correctness & Efficiency
- **Low:** デコレータのネストが深く、若干読みづらい。`click.group` や `click.command` に直接適用する形式は標準的だが、オプションの追加順序がコマンドのヘルプ表示順に影響するため注意が必要。

## 4. mylog.py

### Type Safety
- **Low:** `loggerInit` の `out` 引数に型ヒントがない。

## 5. __init__.py

### Logic Correctness & Efficiency
- **Medium:** `__all__` に `ESQ_EL2` などが含まれていないものがある（`ESQ_EL1` など）。エクスポートする定数の一貫性を確認すべき。

## 6. __main__.py

### Logic Correctness & Efficiency
- **High:** `pomodoro` コマンド内のループ。`while True` の中で `BaseTimer` を毎回インスタンス化している。`KeyboardInterrupt` 時のクリーンアップ処理が各所で重複している。
- **Medium:** `ESQ_CSR_OFF` を `try` の外で出力している箇所がある。例外発生時にカーソルが消えたままになるリスクがある。

### Type Safety
- **Medium:** `ctx` 引数に型ヒントがない。

## 7. tests/

### Test Quality
- **High:** `BaseTimer` の `main` ループのテスト (`test_main_loop_simple`) において、`side_effect` で渡している `time.monotonic` の値がループ回数と密結合しており、実装の微細な変更（ループ内での `time.monotonic` 呼び出し回数増など）で壊れやすい。
- **Medium:** `test_responsive_layout` において、`all(col.use for col in base_timer.col.values())` のアサーションがあるが、初期状態が `True` であることを前提としている。
- **Medium:** `ProgressBar` のテスト (`test_get_str_dynamic_bar_len`) で、実装の `round` による挙動に合わせて期待値をコード内で書き換えている。テストが実装の「現状」を追認する形になっており、本来期待すべき仕様（境界条件など）の検証が弱い。
- **Low:** `test_base_timer.py` の `mock_terminal` フィクスチャなどで `yield mock` を使っているが、`with patch(...)` のスコープ管理とフィクスチャのライフサイクルが重複気味。

### Coverage & Completeness
- **Critical:** `src/tmr/__main__.py`, `src/tmr/click_utils.py`, `src/tmr/mylog.py` のカバレッジが 0% である。これらのモジュールの動作確認を行うテストが一切存在しない。特に `click` コマンドライン引数のパースや `pomodoro` の状態遷移ロジックはテストが必要。
- **Medium:** `BaseTimer` の `ring_alarm` が別スレッドで実行されるため、標準的なテストでは例外が発生しても検知しにくい。

## 8. 全体的な設計アーキテクチャ

### 依存関係とモジュール構成
- **良好な点:** `BaseTimer` と `ProgressBar` が分離されており、責務がある程度分かれている。`click_utils` や `mylog` など、共通機能をモジュール化しようとする意図が見える。
- **改善点:** `BaseTimer` が `click` や `blessed (Terminal)` に強く依存しており、ビジネスロジックと表示ロジックが混在している。将来的に GUI や Web インターフェースに対応する場合、大幅なリファクタリングが必要になる。
- **改善点:** `__main__.py` に CLI のコマンド定義と、ポモドーロの制御ロジックが混在している。ポモドーロのステートマシン自体を `BaseTimer` のサブクラスや別クラスとして切り出すことで、テストが容易になる。

### 拡張性とメンテナンス性
- **改善点:** 設定（色、時間、アラームパラメータなど）がクラス定数やデフォルト引数として散在している。設定ファイル（TOML等）から読み込めるような仕組みがあると、より使いやすくなる。
- **改善点:** エラーハンドリング。現状 `KeyboardInterrupt` は捕捉されているが、端末サイズの極端な変更や、入出力エラーに対する考慮が不足している。

### 設計思想
- **総評:** CLI ツールとして、シンプルかつ実用的な機能を `click` と `blessed` を活用して効率的に実装している。一方で、シングルスレッドでのループ処理と `threading` によるアラームの組み合わせにおいて、リソース管理（スレッドの停止）に若干の危うさがある。
- **今後の方向性:** ロジック（タイマーの計算、ポモドーロの遷移）と、表示（CLI, ProgressBar）の抽象化レイヤーを設けることで、コードの堅牢性とテスト可能性が向上する。
