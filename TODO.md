# TODO

**残っている項目: TODO-006。** これまでに 5 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-007` から。**

---

## TODO-006. `CLAUDE.md` を `~/.claude/CLAUDE.md` の規約に合わせて整理する

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort medium | main のみ |

- [ ] 「## タスク管理」節（`CLAUDE.md:167-171`）を削る
- [ ] 補足から `TBD.md` を落とす
- [ ] 補足の README の記述を直す

プロジェクトの `CLAUDE.md` を `~/.claude/CLAUDE.md` と突き合わせたところ、
ずれが 3 箇所あった。

- 「## タスク管理」節は、`~/.claude/CLAUDE.md` の「TODO.md でのタスク管理」の
  一部を写したもの。写した先が古くなるだけで、プロジェクト固有の事情は
  足されていない。節ごと削る（案内の 1 行も置かない）
- 補足が挙げている `TBD.md` は、もう無い
- 補足の「`README.md` の `timer` の help に `--title` / `--title-color` が
  載っていない」は事実と違う。`README.md:83-85` に載っている。
  「オプションを変えたら README も直す」という規約だけ残す

文書だけを変える項目で、確かめる中身は事実確認と書式が揃っているかだけ
なので、担当は `main のみ`（`~/.claude/CLAUDE.md` の例外に当たる）。

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-005.** `mylog.setLevel()` で変えた水準を既定に戻す API を足す](archives/todo/TODO-005.%20mylog.setLevel()%20で変えた水準を既定に戻す%20API%20を足す.md)
- [**TODO-004.** `getLogger()` の名前を `__qualname__` から取る](archives/todo/TODO-004.%20getLogger()%20の名前を%20__qualname__%20から取る.md)
- [**TODO-003.** ログの水準を、クラスごとに指定できるようにする](archives/todo/TODO-003.%20ログの水準を、クラスごとに指定できるようにする.md)
- [**TODO-002.** ログの水準を、クラス・モジュールごとに変えられるようにする](archives/todo/TODO-002.%20ログの水準を、クラス・モジュールごとに変えられるようにする.md)
- [**TODO-001.** 設定ファイル（`~/.config/tmr/config.toml`）から既定値を読む](archives/todo/TODO-001.%20設定ファイル（~-.config-tmr-config.toml）から既定値を読む.md)

---

## 補足

`archives/` 直下にある `20260211-*.md` などは、この運用を始める前の
過去の記録。**今後は参照しない**（`archives/todo/` とは別物）。
