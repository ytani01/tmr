import click
import threading
from rich.progress import Progress, TaskID
from rich.console import Console
import time

console = Console()

def alarm(count=3):
    """Alarm."""
    for i in range(count):
        click.echo("\a", nl=False)
        time.sleep(.5)
        click.echo("\a", nl=False)
        time.sleep(1.5)

def ring(count=3):
    """Ring."""
    th = threading.Thread(target=alarm, args=(count,), daemon=True)
    th.start()

# 基本的なプログレスバーの作成
def basic_progress():
    total_min = 0.05
    t0 = time.time()
    # ring()
    with Progress(expand=False) as progress:
        task = progress.add_task("task", total=total_min*60)
        while not progress.finished:
            dt = time.time() - t0
            desc_str = f"[green]WORK..[/green]: {dt:4.0f}/{total_min*60:.0f}: "
            progress.update(task, completed=dt, description=desc_str)

            time.sleep(.1)

    ring(5)
    click.pause()

    with Progress() as progress:
        task = progress.add_task("[green]処理中...", total=100)
        for i in range(100):
            time.sleep(0.1)  # タスクをシミュレート
            progress.update(task, advance=1)

# 複数のタスクを同時に表示
def multi_task_progress():
    with Progress() as progress:
        task1 = progress.add_task("[red]タスク1", total=100)
        task2 = progress.add_task("[green]タスク2", total=100)
        task3 = progress.add_task("[blue]タスク3", total=100)

        while not progress.finished:
            progress.update(task1, advance=0.5)
            progress.update(task2, advance=0.3)
            progress.update(task3, advance=0.9)
            time.sleep(0.02)

# カスタムコラムを持つプログレスバー
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

def custom_progress():
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn()
    ) as progress:
        task = progress.add_task("[cyan]カスタムタスク", total=1000)
        for i in range(1000):
            time.sleep(0.01)
            progress.update(task, advance=1)

# 実行
console.print("[bold]基本的なプログレスバー:[/bold]")
basic_progress()

console.print("\n[bold]複数タスクのプログレスバー:[/bold]")
multi_task_progress()

console.print("\n[bold]カスタムプログレスバー:[/bold]")
custom_progress()
