import os
import datetime
import webclass
import general as g
import settings as s
from rich.panel import Panel
from rich.text import Text


def main():
    title = Text("WBCONV_REQ_P", style="bold magenta")
    subtitle = Text("WebClass 課題・教材ダウンローダー", style="dim")
    g.console.print(Panel.fit(Text.assemble(title, "\n", subtitle), border_style="magenta"))

    g.putlog(f"=======================Today:{datetime.datetime.now()},=======================")
    g.putlog("WBCONV_REQ_P made by ktsgsg.")

    os.makedirs(webclass.defaultpath, exist_ok=True)
    userdata = s.getpsw()

    wbc = webclass.webclass(userdata["userid"], userdata["password"])
    source = wbc.session.get(wbc.url)
    webclass.getClasses(source.text, wbc.session)


if __name__ == "__main__":
    main()
