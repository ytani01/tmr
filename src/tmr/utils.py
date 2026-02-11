#
# (c) 2026 Yoichi Tanibayashi
#
import click

from . import ESQ_CSR_OFF, ESQ_CSR_ON, ESQ_EL2


class TerminalContext:
    """端末のカーソル制御と終了処理を行うコンテキストマネージャ"""

    def __enter__(self):
        # カーソルを消す
        click.echo(ESQ_CSR_OFF, nl=False)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # 例外発生時も含め、必ずカーソルを表示に戻す
        click.echo(f"{ESQ_CSR_ON}", nl=False)

        if exc_type is KeyboardInterrupt:
            # KeyboardInterrupt はここで処理し、スタックトレースを出さずに終了
            click.echo(f"\n{ESQ_EL2}Aborted.")
            return True  # 例外を抑制
