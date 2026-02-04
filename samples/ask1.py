from rich import print
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel

console = Console()

# 基本的なテキスト入力プロンプト
def basic_prompt():
    name = Prompt.ask("あなたの名前を入力してください")
    print(f"こんにちは、[bold]{name}[/bold]さん！")

# 確認プロンプト
def confirmation_prompt():
    if Confirm.ask("続行しますか？"):
        print("処理を続行します。")
    else:
        print("処理を中止しました。")

# 数値入力プロンプト
def number_prompt():
    age = IntPrompt.ask("あなたの年齢を入力してください", default=20)
    print(f"入力された年齢: [bold]{age}[/bold]歳")

# パスワード入力プロンプト
def password_prompt():
    password = Prompt.ask("パスワードを入力してください", password=True)
    print("パスワードが入力されました。")

# 選択肢プロンプト
def choice_prompt():
    choices = ["赤", "青", "緑", "黄"]
    color = Prompt.ask("好きな色を選んでください", choices=choices)
    print(f"選択された色: [bold]{color}[/bold]")

# プログレスバー付きの入力プロンプト
def prompt_with_progress():
    from rich.progress import Progress
    import time

    name = Prompt.ask("あなたの名前を入力してください")
    
    with Progress() as progress:
        task = progress.add_task("[green]処理中...", total=100)
        for i in range(100):
            time.sleep(0.05)
            progress.update(task, advance=1)
    
    print(f"[bold]{name}[/bold]さん、処理が完了しました！")

# スタイル付きのプロンプト
def styled_prompt():
    console.print(Panel("ユーザー登録", style="bold magenta"))
    name = Prompt.ask("名前", default="ゲスト")
    email = Prompt.ask("メールアドレス")
    age = IntPrompt.ask("年齢", default=20)
    
    console.print(Panel(f"""
[bold]登録情報:[/bold]
名前: {name}
メールアドレス: {email}
年齢: {age}歳
    """, title="登録情報", border_style="green"))

# 実行
console.print("[bold]基本的なテキスト入力プロンプト:[/bold]")
basic_prompt()

console.print("\n[bold]確認プロンプト:[/bold]")
confirmation_prompt()

console.print("\n[bold]数値入力プロンプト:[/bold]")
number_prompt()

console.print("\n[bold]パスワード入力プロンプト:[/bold]")
password_prompt()

console.print("\n[bold]選択肢プロンプト:[/bold]")
choice_prompt()

console.print("\n[bold]プログレスバー付きの入力プロンプト:[/bold]")
prompt_with_progress()

console.print("\n[bold]スタイル付きのプロンプト:[/bold]")
styled_prompt()
