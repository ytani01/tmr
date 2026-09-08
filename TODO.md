# TODO

**残っている項目: TODO-016, TODO-017。**
これまでに 15 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-018` から。**

---

## TODO-016. アラームで外部コマンドを呼べるようにする

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort high | implementer + verifier + reviewer |

- [ ] `AlarmParams` に `cmd: str | None = None` を足す
- [ ] `Timer.thr_alarm()` で、`cmd` があればビープの代わりにコマンドを実行する
- [ ] CLI に `--alarm-cmd` / `--cmd` を足す（`timer` / `pomodoro` 共通）
- [ ] テストを足す
- [ ] `README.md` の help 出力と `docs/User.md` を直す

ベル（`\a`）だけでは気づかないことがあるので、音声ファイルの再生や
デスクトップ通知を任意のコマンドで呼べるようにする。

決めたこと（着手前に利用者と確認済み）:

- **`cmd` を指定したらビープは鳴らさない**（置き換え）。未指定なら従来どおり
- **タイムアップ時に 1 回だけ実行する**（`count` 回は繰り返さない）
- **シェル経由**（`subprocess.run(cmd, shell=True)`）。パイプやリダイレクトを
  書けるようにするため。設定ファイルに書いた文字列がそのままシェルへ渡ることは
  `docs/User.md` に注意として書く
- **ポモドーロは全フェーズ共通で 1 つ**（work / break で分けない）
- **コマンドを実行したあともキー入力を待つ。** 従来のビープ（既定 999 回＝
  実質鳴り続ける）と体感を揃える。ポモドーロはキーを押すまで次のフェーズへ
  進まない
- **コマンドの終了はアラーム用の daemon スレッドの中で待つ**（`subprocess.run`）。
  メインループは止まらず、終了コードもログに残せる
- **失敗しても（コマンドが無い、非ゼロ終了）ログに残して続行する**

---

## TODO-017. 文書全体を現在の実装と照らして見直す

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort high | verifier + wording |

- [ ] `CLAUDE.md`（プロジェクト）の設計記述のずれを直す
- [ ] `README.md` を現在の実装と照らす
- [ ] `docs/User.md` を現在の実装と照らす
- [ ] `docs/Developer.md` を現在の実装と照らす
- [ ] 書いたとおりに試せる手順・コマンド例を実際に動かして確かめる

**TODO-016 の完了後に着手する**（外部コマンドの実装が固まってから）。

`TODO-015` で文書を整備したあと、`TODO-016` で実装が動いた。
外部コマンドの件に限らず、**文書全体を現在の実装と照らして見直す**。

reviewer が `TODO-016` で見つけた `CLAUDE.md` のずれ（起点。詳細は
[reviewer-report.md](archives/agents/TODO-016/reviewer-report.md) の指摘 4）:

- 「アラームの鳴らし方は `AlarmParams(count, sec1, sec2)`」— フィールドが増えた
- 「停止の合図は `alarm_active` フラグ 1 つ（スレッド側もメインループ側も
  見ている）」— 外部コマンドの経路ではスレッド側が見ない。
  **今回いちばん設計が動いた所**なので 1 行では足りない
- 値の検証の節（「二重の作り」）に `cmd` の扱いを反映する

決めておくこと:

- **`CLAUDE.md` と `docs/Developer.md` の書き分け。** 今は同じ設計の説明が
  両方にある。どちらを正とし、もう一方から何を消すかを、着手時に決める

分担: 実装（コード）を変えない項目なので、`implementer` は立てない。
文書に書かれた手順が実際に動くかの再現を `verifier`、文面の推敲を
`wording` に分ける。**手順の再現は main が兼ねない**（書いた本人は
「書いたとおり」と読んでしまう）。

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-015.** `README.md` と `docs/User.md`, `docs/Developer.md` を整備](archives/todo/TODO-015.%20`README.md`%20と%20`docs-User.md`,%20`docs-Developer.md`%20を整備.md)
- [**TODO-014.** `pomodoro.py` のログと、点滅表示のテストを足す](archives/todo/TODO-014.%20pomodoro.py%20のログと、点滅表示のテストを足す.md)
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
