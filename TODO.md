# TODO

**残っている項目: TODO-014, TODO-015。**
これまでに 13 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-016` から。**

---

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

## TODO-015. `README.md` と `docs/User.md`, `docs/Developer.md` を整備

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort high | implementer + verifier |

- [ ] `README.md` — 紹介と特徴のアピールに絞る。インストール、簡単な
      使用例、`docs/User.md` / `docs/Developer.md` への導線。
      `docs/fig1.png` を活かす
- [ ] `docs/User.md` — 利用者向け。`timer` / `pomodoro` のオプション、
      キー操作、設定ファイル（`~/.config/tmr/config.toml`）、画面の見方
      （幅が狭いときの省略）。今 `README.md` にある help 出力と
      設定ファイルの節はこちらへ移す
- [ ] `docs/Developer.md` — 開発者向け。`TimerClock` / `TimerView` /
      `Timer` の 3 分割、`PomodoroTimer` が継承しない理由、`col_list()` と
      `priority`、`mylog` の規約、テストの patch 先、開発コマンド
- [ ] **図を作って各文書に入れる**（文章だけで説明しない）。mermaid を
      基本とし、画面の並びのように mermaid が向かないものは枠線付きの
      テキスト図にする
  - `README.md`: ポモドーロのサイクル（作業 → 休憩 → …）の流れ図。
    パッと見て何をするツールか分かるもの
  - `docs/User.md`: 画面の各項目が何を指すかの図（`title` / 残り時間 /
    経過率 / `pbar` などの位置と意味）。幅が狭いときに `priority` の
    低い列が落ちていく様子の図
  - `docs/Developer.md`: クラス構成（`Timer` が `TimerClock` /
    `TimerView` / `Terminal` を持ち、`PomodoroTimer` が `Timer` を
    順に呼ぶ）の図。`Timer.main()` のループと、`main()` の戻り値・
    `next` によるフェーズ制御の状態遷移図。`col_list()` から表示が
    決まる流れの図
- [ ] 3 文書の重複を無くす（同じことを 2 箇所に書かない。`CLAUDE.md` とは
      役割を分ける — `CLAUDE.md` は Claude 向けの規約、`Developer.md` は
      人間向けの構造説明）
- [ ] `README.md` / `docs/User.md` に載せるコマンド例と help 出力が、
      実際の出力と一致するか確かめる。mermaid が実際に描画できるかも
      確かめる

新しいスクリーンショットは撮らず、既存の `docs/fig1.png` と、上の図で
説明する。

**分担の理由**: 文書だけの項目だが、インストール手順・コマンド例・
help 出力は書いたとおりに試せるので、再現の確認は `verifier` に分ける
（`~/.claude/CLAUDE.md` の TODO-017）。mermaid の構文が通るかもここで
見る。挙動は変わらないので `reviewer` は入れない。3 ファイルにまたがる
ので執筆は `implementer` に出し、main は構成と図の設計、
`Developer.md` の内容設計を持つ。

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-013.** `ProgressBar` が古い `t_limit` を持ち続ける](archives/todo/TODO-013.%20ProgressBar%20が古い%20t_limit%20を持ち続ける.md)
- [**TODO-012.** 0 分・0 サイクルを指定すると壊れる](archives/todo/TODO-012.%200%20分・0%20サイクルを指定すると壊れる.md)
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
