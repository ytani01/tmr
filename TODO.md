# TODO

**残っている項目: TODO-012, TODO-013, TODO-014。**
これまでに 11 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-015` から。**

---

## TODO-012. 0 分・0 サイクルを指定すると壊れる

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort medium | implementer + reviewer + verifier |

- [ ] `tmr timer 0` — `TimerClock.rate` が `elapsed / t_limit` でゼロ除算に
      なる（**コードを読んだだけで未再現**。まず再現から）
- [ ] `tmr pomodoro -c 0` — `phases()` が何も yield しないまま
      `while True` を回り続けて固まる
- [ ] どちらも「そもそも受け付けない」のか「0 として動かす」のかを決める。
      CLI で弾くなら `click` の型・コールバックで済む

どちらも TODO-010 より前からあり、分割で持ち込んだものではない
（TODO-010 の reviewer が読んで気づいた）。

## TODO-013. `ProgressBar` が古い `t_limit` を持ち続ける

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort medium | implementer + reviewer + verifier |

- [ ] `TimerView.display()` は毎回 `clock.t_limit` を読むのに、
      `ProgressBar` は `__init__` 時点の値を持ったままなので、両者が
      食い違うとプログレスバーの目盛りだけが古い値で描かれる
- [ ] `TimerView` が `t_limit` を持たず、`display()` の中で
      `clock.t_limit` を `ProgressBar` へ渡す形にできないか見る
      （`ProgressBar` の API を変えることになる）

今は `Timer.__init__` が同じ値を両方へ渡すので実害は無い。
`tests/test_view.py` が `clock.t_limit` を後から書き換えていて、
**テストの中では既にずれた状態を作っている**（`ProgressBar` が
モックなので露見していない）。

## TODO-014. `pomodoro.py` のログと、点滅表示のテストを足す

|      | main | 担当 |
|------|------|------|
| 見込み | Sonnet 5 / effort medium | implementer + verifier |

- [ ] `PomodoroTimer` にクラス本体の `__log = getLogger(__qualname__)` が
      無い（`CLAUDE.md` のログ規約から漏れている唯一のクラス）。
      TODO-010 で足した `phases()` はクラスの外にあるので、
      モジュール先頭の `_log` が要る
- [ ] `TimerView.display()` の点滅（`pause_blink` の列と、満了時の
      `state`）に直接のテストが無い。`CLAUDE.md` に書いてある仕様なので
      1 件足しておく

どちらも挙動は変わらない。

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-010.** `Timer` を分割し、引数をデータクラスにする](archives/todo/TODO-010.%20Timer%20を分割し、引数をデータクラスにする.md)
- [**TODO-011.** `docs/mylog.md` を消し、`mylog.py` の docstring に寄せる](archives/todo/TODO-011.%20docs-mylog.md%20を消し、mylog.py%20の%20docstring%20に寄せる.md)
- [**TODO-009.** モジュール構成を整理する（移動と改名だけ）](archives/todo/TODO-009.%20モジュール構成を整理する（移動と改名だけ）.md)
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
記録。**今後は参照しない**（`archives/todo/` とは別物）。
