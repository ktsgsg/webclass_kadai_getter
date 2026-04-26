import urllib
import urllib.parse
import os
import webclass
import general as g

"""
PDFを指定のフォルダにダウンロードします．
"""


def get_qstn_fileurl(query_str):
    query = urllib.parse.parse_qs(query_str)
    file = query["file"]
    filetype = "pdf" if ".pdf" in file[0] else "other"
    fileurl = webclass.webclassurl + file[0]
    return [filetype, fileurl]


def get_fileurl(query_str):
    query = urllib.parse.parse_qs(query_str)
    contents_url = query["contents_url"]
    file = query["file"]
    filetype = "pdf" if ".pdf" in file[0] else "other"
    fileurl = webclass.webclassurl + contents_url[0] + file[0]
    return [filetype, fileurl]


def downloadpdf(url, session, filepath):
    source = session.get(url)
    with open(filepath, "wb") as file:
        file.write(source.content)


def getfiles(query, session, filepath, label=None):
    label = label or os.path.basename(filepath)
    fileurl = []
    if "/webclass/loadit.php" in query:
        fileurl = get_qstn_fileurl(query)
    if "/webclass/txtbk_show_text.php" in query:
        fileurl = get_fileurl(query)

    g.putlog(f"fileurl:{fileurl}")

    if not fileurl:
        g.content_skip(label, "URLを解決できませんでした")
        return

    if fileurl[0] == "pdf":
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            g.putlog(f"skip (already exists):{filepath}")
            g.content_cached(label, filepath)
            return
        try:
            downloadpdf(fileurl[1], session, filepath)
            g.putlog(f"filepath:{filepath}")
            g.content_ok(label, filepath)
        except Exception as e:
            g.putlog(f"download error:{e}")
            g.content_err(label, "ダウンロード失敗")
    else:
        g.content_skip(label, "PDF以外のため未対応")
