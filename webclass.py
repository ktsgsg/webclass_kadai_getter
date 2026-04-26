import urllib.parse
import requests
import json
import urllib
from bs4 import BeautifulSoup
import os
import general as g
import filedownload
import auth_token as ath

defaultpath = "class"
webclassurl = "https://rpwebcls.meijo-u.ac.jp"


def getacs(source):
    soup = BeautifulSoup(source, "html.parser")
    exccode = soup.find("script").string
    acsPath = exccode.split('"')[1].replace('&amp;', "&")
    return acsPath


class webclass:
    def __init__(self, userid, password):
        self.session = requests.Session()
        with g.console.status("[info]ログイン中...[/]", spinner="dots"):
            tokenId = ath.getToken(userid, password)
            url = "https://rpwebcls.meijo-u.ac.jp/webclass/login.php?auth_mode=SAML"
            res = self.session.get(url, allow_redirects=False)
            location = res.headers["Location"]
            self.session.cookies.set("iPlanetDirectoryPro", tokenId)
            wbres = self.session.get(location)
            g.truetatuscode(wbres.status_code, 200)
            soup = BeautifulSoup(wbres.text, "html.parser")
            responsedatas = soup.find_all("input")
            SAMLResponse = responsedatas[0].attrs["value"]
            RelayState = responsedatas[1].attrs["value"]
            data = {
                "SAMLResponse": SAMLResponse,
                "RelayState": RelayState,
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            req = urllib.parse.urlencode(data)
            defaultsp = "https://rpwebcls.meijo-u.ac.jp/simplesaml/module.php/saml/sp/saml2-acs.php/default-sp"
            self.session.post(defaultsp, headers=headers, data=req, allow_redirects=False)
            g.putlog("SAMLAuthToken acquired")
            g.putlog(dict(self.session.cookies))

            loginphp = self.session.get(url, allow_redirects=False)
            acsPath = getacs(loginphp.text)
            g.putlog(dict(self.session.cookies))

            webclassurl_ = webclassurl + acsPath
            webclasresponce = self.session.get(webclassurl_)
            g.truetatuscode(webclasresponce.status_code, 200)
            self.url = webclassurl_
        g.success("ログインに成功しました")


def responceacspath(url, session):
    source = session.get(url)
    acspath = getacs(source.text)
    responce = session.get(webclassurl + acspath)
    g.truetatuscode(responce.status_code, 200)
    return responce


def getshowinfopagecontent(soup: BeautifulSoup, session):
    g.putlog("getshowinfopagecontent")
    g.putlog(soup.prettify)
    path = soup.find("frame", {"name": "contentsInfo"})["src"].replace("&amp;", "&")
    url = webclassurl + "/webclass/" + path
    header = {"content-type": "application/x-www-form-urlencoded"}
    data = {"next": "%E9%96%8B%E5%A7%8B"}
    req = urllib.parse.urlencode(data)
    responce = session.post(url, headers=header, data=req)
    soup = BeautifulSoup(responce.text, "html.parser")
    g.putlog(soup.prettify)
    execode = soup.find("script").string
    execode = execode.split('"')[1].replace("&amp;", "&")
    url = webclassurl + execode
    source = session.get(url)
    g.putlog(source.text)

    soup = BeautifulSoup(source.text, "html.parser")
    execode = soup.find("script").string
    execode = execode.split('"')[1].replace("&amp;", "&")
    url = webclassurl + "/webclass/" + execode
    source = session.get(url)
    g.putlog(source.text)
    return source


def getcontents(sectionelement: BeautifulSoup, session, classname):
    title = sectionelement.find("h4", class_="panel-title").get_text()
    g.putlog(f"コース名,{title}")
    courcename = title
    no_courcename = False
    if courcename == "" or courcename == " ":
        no_courcename = True
        courcename = "(無題)"

    g.course_line(courcename if courcename.strip() else "(無題)")

    contentselements = sectionelement.find(class_="list-group").find_all(
        "section", class_="cl-contentsList_listGroupItem"
    )
    for j in range(len(contentselements)):
        contentname = "(unknown)"
        try:
            contenttitle = contentselements[j].find(
                "h4", class_="cm-contentsList_contentName"
            ).find("a")
            contenturl = contenttitle["href"]
            session_qs = urllib.parse.urlparse(contenturl).query
            session_qd = urllib.parse.parse_qs(session_qs)
            contenturl = (
                "https://rpwebcls.meijo-u.ac.jp/webclass/do_contents.php?reset_status=1&"
                + "set_contents_id="
                + session_qd["set_contents_id"][0]
            )
            contentname = contenttitle.get_text()
            g.putlog(f"コンテンツ,{contentname}")

            if no_courcename and j == 0:
                courcename = contentname

            source = session.get(contenturl)
            acspath = getacs(source.text)
            url = webclassurl + "/webclass/" + acspath
            source = session.get(url)
            soup = BeautifulSoup(source.text, "html.parser")
            if "show_frame.php" in acspath:
                source = getshowinfopagecontent(soup, session)
                url = source.url
                soup = BeautifulSoup(source.text, "html.parser")

            g.putlog(f"content:{contentname}")
            g.putlog(f"url:{url}")

            uri = urllib.parse.urlparse(url)
            g.putlog(f"path:{uri.path}")

            if uri.path == "/webclass/qstn_frame.php":
                g.putlog("qtn selected")
                anserpath = soup.find("frame", {"name": "answer"})["src"]
                g.putlog(f"anser path:{anserpath}")
                ansurl = webclassurl + "/webclass/" + anserpath
                source_ans = session.get(ansurl)
                soup = BeautifulSoup(source_ans.text, "html.parser")
                g.putlog(soup.prettify())
                question_path = soup.find("input", {"name": "question_url"})["value"]
                g.putlog(f"question_path:{question_path}")
                query = question_path

                filepath = f"{defaultpath}/{classname}/{courcename}/{contentname}"
                os.makedirs(filepath, exist_ok=True)
                filepath = f"{filepath}/work.pdf"
                filedownload.getfiles(query, session, filepath, contentname)

            elif uri.path == "/webclass/txtbk_frame.php":
                g.putlog("txtbk selected")
                chapterpath = soup.find(
                    "frame", {"name": "webclass_chapter"}
                ).attrs["src"].replace("&amp;", "&")
                chapterurl = webclassurl + "/webclass/" + chapterpath
                source_chapter = session.get(chapterurl)
                soup_chapter = BeautifulSoup(source_chapter.text, "html.parser")
                json_str = soup_chapter.find("script", id="json-data").get_text()
                pagedata = json.loads(json_str)
                text_urls = pagedata["text_urls"]
                g.putlog(f"text_urls:{text_urls}")
                chapternames = getchapternames(soup_chapter, len(text_urls.values()))
                g.putlog(f"chapternames:{chapternames}")

                for i in range(len(chapternames)):
                    filepath = f"{defaultpath}/{classname}/{courcename}/{contentname}"
                    os.makedirs(filepath, exist_ok=True)
                    filepath = f"{filepath}/{chapternames[i]}.pdf"
                    label = f"{contentname} / {chapternames[i]}"
                    filedownload.getfiles(text_urls[f"{i+1}"], session, filepath, label)
            else:
                g.content_skip(contentname, "未対応のコンテンツ")

        except Exception as e:
            g.putlog(f"error:{e}")
            g.content_skip(contentname)


def getchapternames(soup, page):
    chapters = soup.find_all("span", {"class": "size2 darkslategray"})
    n = page
    chapternames = []
    for i in range(int(n)):
        chaptername = chapters[i * 2].get_text() + "," + chapters[i * 2 + 1].get_text()
        chapternames.append(chaptername)
    return chapternames


def getsections(page, session):
    divs = page.find_all("div")
    for n in divs:
        n.extract()
    name = page.get_text()
    classname = name[9:]
    g.putlog(f"授業名:{classname}")
    g.class_line(classname)
    classurl = webclassurl + page["href"]
    os.makedirs(defaultpath + "/" + classname, exist_ok=True)

    source = responceacspath(classurl, session)
    soup = BeautifulSoup(source.text, "html.parser")
    sectionelements = soup.find_all("section", class_="cl-contentsList_folder")
    for i in range(len(sectionelements)):
        getcontents(sectionelements[i], session, classname)
    g.kugiri()


def getClasses(page, session):
    soup = BeautifulSoup(page, "html.parser")
    schedule_element = soup.find(id="schedule-table")
    hrefs = schedule_element.find_all("a", href=True)
    g.info(f"{len(hrefs)} 件の授業が見つかりました")
    for href in hrefs:
        getsections(href, session)
    g.console.print()
    g.success("すべての処理が完了しました")
