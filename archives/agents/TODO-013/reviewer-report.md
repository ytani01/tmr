# TODO-013 レビュー報告

対象: 未コミットの `git diff`（`src/tmr/progress_bar.py`,
`src/tmr/timer.py`, `src/tmr/view.py`, `tests/test_progress_bar.py`,
`tests/test_timer.py`, `tests/test_view.py`, `TODO.md`）。

## 結論

要修正は無し。設計の意図（`ProgressBar` が `total` を状態として
持たない）どおりに実装されており、分岐の意味も変わっていない。
検討事項を 2 件、情報として 1 件挙げる。

## 検討

1. **`total` を位置引数のままにした判断について**
   `ProgressBar.get_str()` / `display()` の `total` は `*` より前の
   位置引数のままで、`bar_len` / `stop` のようにキーワード専用には
   していない（`src/tmr/progress_bar.py:38-42`, `78-82`）。
   `val` と対になる必須値という点では `val, total` の並びは自然で、
   呼び出し側（`view.py:172-177`、テスト各所）もすべて位置引数で
   揃っているため、今のままで実害は無い。ただし `get_str(val, total)`
   は呼び出し側だけを見ると `total` が何かがコード上分かりにくい
   （`bar_len=`, `stop=` はキーワードで分かるのに `total` だけ位置）。
   `total` をキーワード専用にすべきだったかは好みの範囲に近いが、
   一貫性の観点で一考の余地はある（未確認: 設計判断の記録が
   TODO-013 のファイルや commit メッセージに残っているかは見ていない）。

2. **`TODO.md` の「見込み」欄が実装後に書き換わっている**
   `TODO-013` は `a40cc83`（立てたコミット）で
   `見込み: implementer + reviewer + verifier` として登録されたが、
   今回の diff で `reviewer + verifier` に変わっている
   （`TODO.md` の diff）。`~/.claude/CLAUDE.md` は「分担は、項目を
   立てるときに決めて見込みの行へ書く」としており、実装後に
   欄を書き換えること自体を禁じてはいないが、**いつ・なぜ
   implementer を外したか**が diff からは読み取れない
   （main が自分で実装した、という理解で良いか未確認）。
   確認と実装が別サブエージェントである規約（挙動が変わる項目には
   レビュー担当も要る）は reviewer/verifier が別途立っているので
   満たしている。書き換えの経緯を `archives/agents/TODO-013/` の
   どこかに一言残しておくと、あとで TODO.md の履歴だけでは
   分からなくなるのを防げる。

## 情報として

- **分岐・条件式の意味は変わっていない。**
  `rate = val / total if total > 0 else 1.0` と
  `if val >= total or stop:` の 2 箇所は、`self.total` を
  引数 `total` に置き換えただけで、`total <= 0` / `nan` / `inf` の
  扱いも従来と同じ（`src/tmr/progress_bar.py:54`, `61`)。
  実運用では `total` は常に `clock.t_limit` から来て、
  `TimerClock.__init__` が `math.isfinite(t_limit) and t_limit > 0` を
  強制している（`src/tmr/clock.py:25-27`）ため、`ProgressBar` 側で
  異常値に当たる経路は現状無い。`ProgressBar` 自体は独立クラスとして
  境界値のテスト（`test_get_str_edge_cases`）を保っており、この点も
  従来どおり。

- **テストは TODO-013 が指摘した食い違いを実際に捕まえる作りになって
  いる。** `tests/test_view.py` の `test_pbar_uses_current_t_limit` が、
  `clock.t_limit` を後から書き換えたときに
  `mock_pbar.return_value.get_str.call_args[0]` が
  `(30.0, 60.0)` に追随することを確認しており、
  「`TimerView` が古い `t_limit` を渡し続ける」バグそのものを
  再現・検出できる形になっている。`ProgressBar` はモックなので
  ここでは「渡された引数」しか見ていないが、`total` を実際に
  描画に使うかどうかは `tests/test_progress_bar.py` の
  `test_get_str_total_not_kept`（同じ `val` で `total` だけ変えると
  出力が変わることを確認）が別途担っており、2 つを合わせて
  「`TimerView` が最新の `t_limit` を渡す」「`ProgressBar` が
  渡された `total` をそのまま使う」の両方を検証できている。

- **API の呼び出し側はすべて追随できている。**
  `TimerView(term, t_limit, title)` → `TimerView(term, title)`、
  `ProgressBar(total)` → `ProgressBar()`、
  `pbar.get_str(val, ...)` → `pbar.get_str(val, total, ...)` の
  変更を、`src/tmr/timer.py`, `src/tmr/view.py` と
  `tests/test_progress_bar.py`, `tests/test_view.py`,
  `tests/test_timer.py` の呼び出し・アサーションすべてで確認した。
  他に `TimerView(` / `ProgressBar(` / `pbar.get_str(`/`pbar.display(`
  を呼んでいる箇所は `grep` で見た限り無い（`README.md` にも
  これらの API への言及は無い）。

- **行長 78 文字。** 新規追加行のうち、日本語コメント／docstring
  （マルチバイト文字）を含む行を `len()` で数え直したところ、
  すべて 78 文字以内だった（`grep` のバイト単位カウントでは超えて
  見えたが誤検出）。`ProgressBar.get_str()` の docstring
  （`src/tmr/progress_bar.py:44-47`）は、`total` を保持しない理由
  （呼び出しのたびに受け取る設計にした「なぜ」）を書いており、
  `CLAUDE.md` の「何を」ではなく「なぜ」というコメントの方針に沿う。

- **ログ。** `ProgressBar.__init__` のログを
  `total=` から `bar_length=` に直しており、削った引数と整合している
  （`src/tmr/progress_bar.py:27`）。クラス本体の
  `__log = getLogger(__qualname__)` は変更していない。

- **設計の 3 分割（`TimerClock` / `TimerView` / `Timer`）との整合。**
  `TimerView.__init__` から `t_limit` を落とし、`display()` の中で
  毎回 `clock.t_limit` を読む形は、「`TimerView` は `TimerClock` を
  都度参照する」という既存の作り（`CLAUDE.md` の「設計」節、
  `display()` が `clock` を引数に取る形）にむしろ揃った変更に見える。
  `ProgressBar` は 3 分割の外側にある補助クラスで、今回の変更は
  その責務（バーの文字列を作るだけ、状態を持たない）を明確にする
  方向であり、既存の分割方針と矛盾しない。

- **範囲。** diff に含まれるのは `TODO-013` の対象ファイルと
  対応するテストのみで、無関係な変更は見当たらなかった。
