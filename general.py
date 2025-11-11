import sys
#便利にしたいから
def putlog(str):#ログをlog.txtに追記する
    fp = open("log.txt","a")
    fp.write(str+"\n")
    fp.close()

def kugiri():
    print("########################################################")
    
def truetatuscode(statuscode,truestatucode):
    if statuscode != truestatucode:
        print("エラーが発生しました.パソコンがインターネットにつながっていないか，回線が混み合っています．")
        putlog(f"エラー,statuscode:{statuscode}")
        raise Exception(f"正しいstatuscodeではありません.\n statuscode:{statuscode}.\nしばらくしてから起動してください.")

