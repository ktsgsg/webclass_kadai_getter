#!/usr/bin/env python3
"""全PDFまとめフォルダ内のファイル名の漢数字を数字に変換するスクリプト"""

import os
import re

# 対象フォルダ
DIR = "/Users/KeitaYamamoto/Documents/GitHub/webclass_worksgetter/webclass_kadai_getter/class/中国語４ (2025-後期-木1)/全PDFまとめ"

# 漢数字から数字への変換マップ（長いものから順に）
kanji_to_num = [
    ("二十三", "23"),
    ("二十", "20"),
    ("十八", "18"),
    ("十六", "16"),
    ("十五", "15"),
    ("十四", "14"),
    ("十三", "13"),
    ("十二", "12"),
    ("十一", "11"),
    ("十", "10"),
    ("九", "9"),
    ("八", "8"),
    ("七", "7"),
    ("六", "6"),
    ("五", "5"),
    ("四", "4"),
    ("三", "3"),
    ("二", "2"),
    ("一", "1"),
]

def convert_kanji_to_number(filename):
    """ファイル名内の漢数字を数字に変換"""
    result = filename
    for kanji, num in kanji_to_num:
        result = result.replace(kanji, num)
    return result

def main():
    if not os.path.exists(DIR):
        print(f"フォルダが見つかりません: {DIR}")
        return
    
    files = [f for f in os.listdir(DIR) if f.endswith('.pdf')]
    count = 0
    
    for filename in files:
        new_filename = convert_kanji_to_number(filename)
        
        if filename != new_filename:
            old_path = os.path.join(DIR, filename)
            new_path = os.path.join(DIR, new_filename)
            os.rename(old_path, new_path)
            print(f"リネーム: {filename}")
            print(f"      -> {new_filename}")
            count += 1
    
    print(f"\n完了！ {count} 個のファイル名を変換しました。")

if __name__ == "__main__":
    main()
