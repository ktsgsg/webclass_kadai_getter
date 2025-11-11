import urllib
import urllib.parse
import requests
import webclass
import general as g

"""
PDFを指定のフォルダにダウンロードします．
"""

def get_qstn_fileurl(query_str):
    query = urllib.parse.parse_qs(query_str)
    result = []
    file = query["file"]
    if ".pdf" in file[0]:
        result.append("pdf")
    else:
        result.append("other")
    #print(contents_url,file)
    fileurl = webclass.webclassurl + file[0]
    result.append(fileurl)#要素0にはファイルのタイプ 1にはファイルのurl
    return result

def get_fileurl(query_str):
    query = urllib.parse.parse_qs(query_str)
    result = []
    contents_url = ""
    
    contents_url = query["contents_url"]
    file = query["file"]
    if ".pdf" in file[0]:
        result.append("pdf")
    else:
        result.append("other")
    #print(contents_url,file)
    fileurl = webclass.webclassurl + contents_url[0] + file[0]
    result.append(fileurl)#要素0にはファイルのタイプ 1にはファイルのurl
    return result
    
def downloadpdf(url,cookies,filepath):
    source = requests.get(url,cookies=cookies)
    pdfdata = source.content
    file = open(filepath,"wb")
    file.write(pdfdata)
    file.close()

def getfiles(query,cookies,filepath):
    fileurl = []
    if "/webclass/loadit.php" in query:#これがPDFが配信されているパスのURL
        fileurl = get_qstn_fileurl(query)
    if "/webclass/txtbk_show_text.php" in query:
        fileurl = get_fileurl(query)
    
    #print(fileurl)
    if fileurl[0] == "pdf":
        print("Filetype:PDF")
        print(f"Downloading:{fileurl[1]} to {filepath}")
        downloadpdf(fileurl[1],cookies,filepath)
        print("done.")
        g.putlog(f"filepath:{filepath}")
    else:
        print("The file is in a format that cannot be downloaded.")