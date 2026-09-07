#
# (c) 2026 Yoichi Tanibayashi
#
import click

ESC = "\x1b"  # == \033, Escape
ESQ_CSR_ON = f"{ESC}[?25h"  # Visible cursor
ESQ_CSR_OFF = f"{ESC}[?25l"  # Invisible cursor
ESQ_EL0 = f"{ESC}[0K"  # Erase in line: カーソルから行末まで削除
ESQ_EL1 = f"{ESC}[1K"  # Erase in line: 行頭からカーソルまで削除
ESQ_EL2 = f"{ESC}[2K"  # Erase in line: 行全体を削除


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
