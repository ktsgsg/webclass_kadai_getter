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
    soup = BeautifulSoup(source,"html.parser")
    exccode = soup.find("script").string
    acsPath = exccode.split('"')[1].replace('&amp;',"&")
    return acsPath

class webclass:
    def __init__(self,userid,password):
        self.session = requests.Session()
        tokenId = ath.getToken(userid,password)
        url = "https://rpwebcls.meijo-u.ac.jp/webclass/login.php?auth_mode=SAML"
        res = self.session.get(url,allow_redirects=False)
        location = res.headers["Location"]
        self.session.cookies.set("iPlanetDirectoryPro",tokenId)
        wbres = self.session.get(location)
        g.truetatuscode(wbres.status_code,200)
        soup = BeautifulSoup(wbres.text,"html.parser")
        responsedatas = soup.find_all("input")
        SAMLResponse = responsedatas[0].attrs["value"]
        RelayState = responsedatas[1].attrs["value"]
        data = {
            "SAMLResponse": SAMLResponse,
            "RelayState": RelayState
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        req = urllib.parse.urlencode(data)
        defaultsp = "https://rpwebcls.meijo-u.ac.jp/simplesaml/module.php/saml/sp/saml2-acs.php/default-sp"
        self.session.post(defaultsp,headers=headers,data=req,allow_redirects=False)
        g.kugiri()
        print("SAMLAuthToken")
        print(dict(self.session.cookies))
        g.kugiri()
        loginphp = self.session.get(url,allow_redirects=False)
        acsPath = getacs(loginphp.text)
        g.kugiri()
        print(dict(self.session.cookies))
        g.kugiri()
        webclassurl_ = webclassurl + acsPath
        webclasresponce = self.session.get(webclassurl_)
        g.truetatuscode(webclasresponce.status_code,200)
        self.url = webclassurl_


def responceacspath(url,session):
    source = session.get(url)
    acspath = getacs(source.text)
    responce = session.get(webclassurl+acspath)
    g.truetatuscode(responce.status_code,200)
    return responce

def getshowinfopagecontent(soup:BeautifulSoup,session):
    g.putlog("GGGAAA2")#識別するやつ
    g.putlog(soup.prettify)
    path = soup.find("frame",{"name":"contentsInfo"})["src"].replace('&amp;',"&")
    url = webclassurl+"/webclass/"+path
    header ={
        "content-type":"application/x-www-form-urlencoded"
    }
    data = {
        "next":"%E9%96%8B%E5%A7%8B"
    }
    req = urllib.parse.urlencode(data)
    responce = session.post(url,headers=header,data=req)
    soup = BeautifulSoup(responce.text,"html.parser")
    g.putlog("GGGAAA23")
    g.putlog(soup.prettify)
    execode = soup.find("script").string
    execode = execode.split('"')[1].replace('&amp;',"&")
    url = webclassurl+execode
    source = session.get(url)

    g.putlog("GGGAAA234")
    g.putlog(source.text)
    soup = BeautifulSoup(source.text,"html.parser")
    execode = soup.find("script").string
    execode = execode.split('"')[1].replace('&amp;',"&")
    url = webclassurl+"/webclass/"+execode
    source = session.get(url)
    g.putlog("GGGAAA2345")
    g.putlog(source.text)
    return source

def getcontents(sectionelement:BeautifulSoup,session,classname):
    title = sectionelement.find("h4",class_="panel-title").get_text()
    print(f"コース名,{title}")
    g.putlog(f"コース名,{title}")
    courcename = title
    no_courcename = False
    if courcename == "" or courcename == " ":#もしcourcenameが空だったら(味文みたいなやつの場合)
        no_courcename = True #no_courcenameフラグを立てる

    contentselements = sectionelement.find(class_="list-group").find_all("section",class_="cl-contentsList_listGroupItem")#授業内容のグループを取得
    for j in range(len(contentselements)):
        try:
            contenttitle = contentselements[j].find("h4",class_="cm-contentsList_contentName").find("a")#授業内容のグループのタイトルを取得
            contenturl = contenttitle['href']
            session_qs = urllib.parse.urlparse(contenturl).query#クエリパラメータを取得
            session_qd = urllib.parse.parse_qs(session_qs)#クエリパラメータを辞書型に変換
            contenturl = "https://rpwebcls.meijo-u.ac.jp/webclass/do_contents.php?reset_status=1&"+"set_contents_id="+session_qd["set_contents_id"][0]
            print(f"コンテンツ,{contenttitle.get_text()}")
            contentname = contenttitle.get_text()

            if no_courcename and j == 0:
                courcename = contentname #content最初のやつを名前にする

            source = session.get(contenturl)
            acspath = getacs(source.text)
            url = webclassurl+"/webclass/"+acspath
            source = session.get(url)
            soup = BeautifulSoup(source.text,"html.parser")
            if "show_frame.php" in acspath:#移動先が確認画面の場合
                source = getshowinfopagecontent(soup,session)#確認画面後に上書き
                url = source.url
                soup = BeautifulSoup(source.text)

            g.putlog(f"content:{contenttitle.get_text()}")
            g.putlog(f"url:{url}")

            uri = urllib.parse.urlparse(url)
            g.putlog(f"path:{uri.path}")
            if(uri.path == "/webclass/qstn_frame.php"):#パスが課題の場合
                print("qtn selected")
                anserpath = soup.find("frame",{"name":"answer"})["src"]
                g.putlog(f"anser path:{anserpath}")
                ansurl = webclassurl+"/webclass/"+ anserpath
                g.putlog(f"anser path:{ansurl}")
                source_ans = session.get(ansurl)
                soup = BeautifulSoup(source_ans.text,"html.parser")
                g.putlog(soup.prettify())
                print("soup seeing")
                question_path = soup.find("input",{"name":"question_url"})["value"]
                g.putlog(f"question_path:{question_path}")
                query = question_path
                g.putlog(f"query:{query}")

                filepath = f"{defaultpath}/{classname}/{courcename}/{contentname}"
                print(filepath)
                os.makedirs(filepath,exist_ok=True)
                filepath = f"{filepath}/work.pdf"
                filedownload.getfiles(query,session,filepath)

            if(uri.path == "/webclass/txtbk_frame.php"):
                print("txtbk selected")
                chapterpath = soup.find("frame",{"name":"webclass_chapter"}).attrs["src"].replace("&amp;","&")
                g.putlog(f"chapterpath:{chapterpath}")
                chapterurl = webclassurl+"/webclass/"+chapterpath
                source_chapter = session.get(chapterurl)
                soup_chapter = BeautifulSoup(source_chapter.text,"html.parser")#チャプターのhtml取得
                json_str = soup_chapter.find("script",id = "json-data").get_text()
                pagedata = json.loads(json_str)#資料の情報をjson形式で保存
                text_urls = pagedata["text_urls"]
                g.putlog(f"text_urls:{text_urls}")
                chapternames = getchapternames(soup_chapter,len(text_urls.values()))
                g.putlog(f"chapternames:{chapternames}")

                for i in range(len(chapternames)):#chapterごとの操作
                    filepath = f"{defaultpath}/{classname}/{courcename}/{contentname}"
                    print(filepath)
                    os.makedirs(filepath,exist_ok=True)
                    filepath = f"{filepath}/{chapternames[i]}.pdf"
                    filedownload.getfiles(text_urls[f"{i+1}"],session,filepath)

        except:
            print("コンテンツ,閉鎖もしくは予期せぬエラー")

def getchapternames(soup,page):
    chapters = soup.find_all("span",{"class":"size2 darkslategray"})
    n = page
    chapternames = []
    for i in range(int(n)):
        chaptername = chapters[i*2].get_text()+","+chapters[i*2+1].get_text()
        chapternames.append(chaptername)
    return chapternames

def getsections(page,session):
    divs = page.find_all("div")  # divタグを持つ要素を取得
    for n in divs:
        n.extract()
    name = page.get_text()
    classname = name[9:]  # "授業名"の部分を取得
    print(f"授業名:{classname}")
    g.putlog(f"授業名:{classname}")
    classurl = webclassurl+page['href']
    os.makedirs(defaultpath+"/"+classname, exist_ok=True)

    source = responceacspath(classurl,session)#偽リダイレクトの時のアクセス方法
    soup = BeautifulSoup(source.text,"html.parser")
    sectionelements = soup.find_all("section",class_="cl-contentsList_folder")#授業内容の部分を取得
    for i in range(len(sectionelements)):
        getcontents(sectionelements[i],session,classname)
    g.kugiri()

def getClasses(page,session):
    soup = BeautifulSoup(page, "html.parser")
    schedule_element = soup.find(id = "schedule-table")
    hrefs = schedule_element.find_all("a", href=True)
    for href in hrefs:
        getsections(href,session)
