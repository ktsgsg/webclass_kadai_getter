import sys
from rich.console import Console
from rich.theme import Theme

_theme = Theme({
    "info": "cyan",
    "success": "green",
    "warn": "yellow",
    "error": "bold red",
    "muted": "dim",
    "class": "bold magenta",
    "course": "bold cyan",
    "content": "white",
})

console = Console(theme=_theme)


def putlog(str):
    """log.txtにのみ書き出す（ターミナルには出さない）"""
    STDOUT = sys.stdout
    fp = open("log.txt", "a")
    sys.stdout = fp
    print(str)
    fp.close()
    sys.stdout = STDOUT


def kugiri():
    putlog("########################################################")


def truetatuscode(statuscode, truestatucode):
    if statuscode != truestatucode:
        console.print("[error]ネットワークエラー[/] パソコンがインターネットにつながっていないか、回線が混み合っています。")
        putlog(f"エラー,statuscode:{statuscode}")
        raise Exception(
            f"正しいstatuscodeではありません.\n statuscode:{statuscode}.\nしばらくしてから起動してください."
        )


def header(text):
    console.rule(f"[class]{text}[/]", style="magenta")


def info(msg):
    console.print(f"[info]ℹ[/] {msg}")


def success(msg):
    console.print(f"[success]✓[/] {msg}")


def warn(msg):
    console.print(f"[warn]![/] {msg}")


def error(msg):
    console.print(f"[error]✗[/] {msg}")


def class_line(name):
    console.print()
    console.print(f"[class]📚 {name}[/]")


def course_line(name):
    console.print(f"  [course]└─ {name}[/]")


def content_ok(name, detail=None):
    line = f"     [success]✓[/] [content]{name}[/]"
    if detail:
        line += f" [muted]→ {detail}[/]"
    console.print(line)


def content_skip(name, reason="閉鎖もしくは予期せぬエラー"):
    console.print(f"     [warn]–[/] [muted]{name} ({reason})[/]")


def content_err(name, reason):
    console.print(f"     [error]✗[/] [content]{name}[/] [muted]({reason})[/]")
