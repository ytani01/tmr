#
# (c) 2026 Yoichi Tanibayashi
#
"""テスト全体の安全弁。

`Timer` はアラームのコマンドを止めるときに `os.killpg()` を呼ぶ。
モックの `pid` をそのまま渡すと、開発機の**無関係なプロセスグループ**へ
シグナルを撃ちうるので、テストの間は常に塞いでおく。

個別のテストで呼び出しを見たいときは、`tests/test_timer.py` の
`mock_killpg` fixture（内側で patch し直す）を使う。
"""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def block_killpg():
    """テスト中は `os.killpg()` を実行させない。"""
    with patch("tmr.timer.os.killpg") as mock:
        yield mock
