# TODO-012 reviewer への追加依頼（2 回目のレビュー）

先の報告（`reviewer-report.md`）を受けて、管理者が 4 件を取り込むと決め、
implementer が実装した。**その追加分だけ**をレビューしてほしい。
コードは直さない。

## 何を取り込んだか

| 報告の番号 | 対応 |
|---|---|
| 1（`nan` / `inf`） | 今回一緒に直した |
| 2（検証の置き場所） | `PomodoroConfig.__post_init__` に集約。`_phases()` 分割は取り消し |
| 3（`t_limit` の後からの代入） | **TODO-013 に回す。今回は手を入れない**（指摘不要） |
| 4（CLI テストの強化） | 対応した |
| 5（`CLAUDE.md` への追記） | 対応した |

依頼の全文は `archives/agents/TODO-012/implementer-task2.md`、
実装者の報告は `archives/agents/TODO-012/implementer-report2.md`。

## 特に見てほしい点

- `PomodoroConfig.__post_init__` の検証が**過不足ないか**。
  `getattr` でフィールド名を回す書き方が読みやすいか、
  フィールドを足したときに漏れないか
- `phases()` をジェネレータに戻したことで、**`cycles < 1` の無限ループが
  本当に再発しないか**。`PomodoroConfig` を経由せず `phases()` に
  不正な config を渡せる経路が無いか（dataclass は構築後に
  `config.cycles = 0` と代入できる点も含めて）
- `cli.py` の `_reject_non_finite` コールバックが、
  **設定ファイル（`default_map`）由来の値にも効くか**。
  `XDG_CONFIG_HOME` を差し替えて `work-time = nan` を実際に試すこと
- `_reject_non_finite` のエラーメッセージ（`must be finite: nan`）が
  どう表示されるか。パラメータ名が出るか
- 追加・変更されたテストが実際にその分岐を突いているか
- `CLAUDE.md` に足した 4 行が、**事実として正しく**、既存の書き方
  （である調、簡潔）に合っているか。冗長でないか
- 前回「問題が無かった」と確認した点が、この変更で崩れていないか
  （特に `-w 0.1` のような小さい正の小数が通ること）

## 報告

`archives/agents/TODO-012/reviewer-report2.md` に書く。
重要度の高い順。問題が無ければ無いと書く。返事は 5 行以内。
