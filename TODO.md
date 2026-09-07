# TODO

**残っている項目: TODO-009, TODO-010。** これまでに 8 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-011` から。**

---

## TODO-009. モジュール構成を整理する（移動と改名だけ）

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort high | implementer + verifier |

- [ ] `base_timer.py` → `timer.py`、`BaseTimer` → `Timer`
- [ ] `utils.py` → `terminal.py`（`ESQ_*` 定数もここへ移す）
- [ ] `timefmt.py` を新設。`SEC_MIN` / `MIN_HOUR` と、`display()` 内ローカルの
      `t_str()` をモジュール関数に出す
- [ ] `__init__.py` は `__version__` だけにする
- [ ] `cli.py` を新設して click のコマンド定義を移し、`__main__.py` は
      entry point だけにする
- [ ] テストのファイル名と import も追随させる
- [ ] `CLAUDE.md` / `README.md` の記述を直す

挙動は変えない。`t_str()` を出すことで、時刻整形の単体テストが書ける。

`ProgressBar.display()` と `ESQ_EL0` / `ESQ_EL1` は本体から使われていないが、
ライブラリとして使う側のために残す（2026-09-08 に決めた）。

---

## TODO-010. `Timer` を分割し、引数をデータクラスにする

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort high | implementer + reviewer + verifier |

- [ ] `TimerClock`（`clock.py`）を切り出す。経過時間・ポーズ・早送り／巻き戻し。
      端末に依存しないので単体でテストできる
- [ ] `TimerView`（`view.py`）を切り出す。列の定義、幅に応じた省略、スタイル付け
- [ ] 表示順と削除の優先順位を 1 箇所にまとめる（`col_list()` の挿入順 +
      `COL_PRIORITY` の二重管理をやめる）
- [ ] `title: tuple[str, str]` と `alarm_params: tuple[int, float, float]` を
      データクラスにする
- [ ] `PomodoroTimer.run()` から、フェーズの並びを決める部分をジェネレータに
      分離する。桁揃え `f"{tt:16s}"` は表示側へ移す

`Timer` はメインループとキー操作・アラームだけの層になる。

TODO-009 が済んでいることが前提。

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-008.** `display()` 周りのバグと小細工を潰す](archives/todo/TODO-008.%20display()%20周りのバグと小細工を潰す.md)
- [**TODO-007.** テストコードの後始末（mypy のエラーと残骸テスト）](archives/todo/TODO-007.%20テストコードの後始末（mypy%20のエラーと残骸テスト）.md)
- [**TODO-006.** `CLAUDE.md` を `~/.claude/CLAUDE.md` の規約に合わせて整理する](archives/todo/TODO-006.%20CLAUDE.md%20を%20~-.claude-CLAUDE.md%20の規約に合わせて整理する.md)
- [**TODO-005.** `mylog.setLevel()` で変えた水準を既定に戻す API を足す](archives/todo/TODO-005.%20mylog.setLevel()%20で変えた水準を既定に戻す%20API%20を足す.md)
- [**TODO-004.** `getLogger()` の名前を `__qualname__` から取る](archives/todo/TODO-004.%20getLogger()%20の名前を%20__qualname__%20から取る.md)
- [**TODO-003.** ログの水準を、クラスごとに指定できるようにする](archives/todo/TODO-003.%20ログの水準を、クラスごとに指定できるようにする.md)
- [**TODO-002.** ログの水準を、クラス・モジュールごとに変えられるようにする](archives/todo/TODO-002.%20ログの水準を、クラス・モジュールごとに変えられるようにする.md)
- [**TODO-001.** 設定ファイル（`~/.config/tmr/config.toml`）から既定値を読む](archives/todo/TODO-001.%20設定ファイル（~-.config-tmr-config.toml）から既定値を読む.md)

---

## 補足

`archives/` 直下にある `20260211-*.md` などは、この運用を始める前の
過去の記録。**今後は参照しない**（`archives/todo/` とは別物）。
