#import urllib.parse
import requests
import json
#import urllib
#from bs4 import BeautifulSoup
#import time
import os
#import sys
import datetime
import webclass
import general
import settings as s

def main(*args):
   #第一引数に保存するパスを指定可能
   print("Hello, this is webclass_kadai_getter main.py made by ktsgsg.")
   if len(args) >= 1:
      webclass.defaultpath = args[0]
   os.makedirs(webclass.defaultpath,exist_ok=True)                             #資料をダウンロードするフォルダを指定 
   
   wbc = set_webclass()                                                       #パスワードを用いてtokenを取得andSAMLAUthtoken
   source = request_webclass(wbc)                                            #それを用いてリクエスト
   
   webclass.getClasses(source.text,wbc.cookies)                                #PDFの取得開始
   
def set_webclass():
   userdata = s.getpsw()                                                       #パスワードの取得
   wbc = webclass.webclass(userdata["userid"],userdata["password"])            #パスワードを用いてtokenを取得andSAMLAUthtoken
   return wbc

def request_webclass(wbc):
   try:
      source = requests.get(wbc.url,cookies=wbc.cookies)                       #それを用いてリクエスト
   except Exception as e:
      general.putlog(f"Error occurred while requesting webclass: {e}")
      raise e
   return source
   
if __name__ == "__main__":
   main()