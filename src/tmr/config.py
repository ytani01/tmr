#
# (c) 2026 Yoichi Tanibayashi
#
"""設定ファイル（TOML）から、オプションの既定値を読む。

置き場所は ``~/.config/tmr/config.toml``
（``XDG_CONFIG_HOME`` があればそちら）。

読んだ内容は ``click`` の ``default_map`` にそのまま渡す。優先順位は
**コマンドライン引数 > 設定ファイル > コードの既定値** で、これは
``click`` 側が面倒を見てくれる（``Context.default_map``）。

```toml
debug = true          # cli 自身のオプション

[timer]
minutes = 5
title = "Work"
title-color = "green"

[pomodoro]
work-time = 25.0
cycles = 4
```

セクション名はサブコマンドの名前（別名 ``t`` / ``p`` ではなく
``timer`` / ``pomodoro``）。キーは長い方のオプション名から ``--`` を
取ったもの（``--title-color`` なら ``title-color``）。``title_color``
のようにアンダースコアで書いてもよい。

ファイルが無ければ黙ってコードの既定値を使う。**壊れていたらエラーで
終了する**（TOML の構文エラー、知らないセクション、知らないキー）。
"""

import os
import tomllib
from pathlib import Path
from typing import Any

import click

# ここは `loggerInit()` より前（`make_context()` の時点）に動くので、
# ログは出さない。読んだ結果は `cli` 側で `ctx.default_map` として出す。

CONFIG_DIR_NAME = "tmr"
CONFIG_FILE_NAME = "config.toml"


def config_path() -> Path:
    """設定ファイルの場所。"""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / CONFIG_DIR_NAME / CONFIG_FILE_NAME


def _param_names(cmd: click.Command) -> dict[str, str]:
    """コマンドが受け付けるキー名 -> パラメータ名 の対応。

    ``--title-color`` は ``title-color`` でも ``title_color`` でも
    書けるようにする。``--help`` / ``--version`` のように値を渡さない
    ものは対象外。
    """
    names: dict[str, str] = {}
    for param in cmd.params:
        if not param.expose_value or param.name is None:
            continue
        names[param.name] = param.name
        names[param.name.replace("_", "-")] = param.name
    return names


def _section(
    cmd: click.Command, data: dict[str, Any], where: str
) -> dict[str, Any]:
    """1 コマンド分の設定を、パラメータ名をキーにした dict にする。"""
    names = _param_names(cmd)
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key not in names:
            raise click.ClickException(
                f"{config_path()}: {where}: 知らないキー: {key!r}"
            )
        result[names[key]] = value
    return result


def load_config(group: click.Group) -> dict[str, Any]:
    """設定ファイルを読んで、``click`` の ``default_map`` を作る。

    ファイルが無ければ空の dict を返す（コードの既定値がそのまま
    使われる）。壊れていたら ``click.ClickException`` を投げる。
    """
    path = config_path()
    if not path.is_file():
        return {}

    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise click.ClickException(f"{path}: {e}") from e

    # サブコマンドの名前 -> コマンド。別名（t / p）も同じものを指す。
    commands = group.commands
    canonical = {cmd.name for cmd in commands.values() if cmd.name}

    top: dict[str, Any] = {}  # cli 自身のオプション
    sections: dict[str, dict[str, Any]] = {}

    for key, value in data.items():
        if isinstance(value, dict):
            if key not in canonical:
                raise click.ClickException(
                    f"{path}: 知らないセクション: [{key}]"
                )
            sections[key] = value
        else:
            top[key] = value

    default_map = _section(group, top, "(先頭)")
    for info_name, cmd in commands.items():
        if cmd.name in sections:
            default_map[info_name] = _section(
                cmd, sections[cmd.name], f"[{cmd.name}]"
            )

    return default_map


class ConfigGroup(click.Group):
    """設定ファイルを ``default_map`` として読み込む ``Group``。

    ``make_context()`` の時点で読むので、``--help`` や引数の解釈より
    先に効く。サブコマンドの ``Context`` は親の ``default_map`` から
    自分の名前の分を受け取る（``click`` の仕組み）。
    """

    def make_context(
        self,
        info_name: str | None,
        args: list[str],
        parent: click.Context | None = None,
        **extra: Any,
    ) -> click.Context:
        if extra.get("default_map") is None:
            extra["default_map"] = load_config(self)
        return super().make_context(info_name, args, parent, **extra)
