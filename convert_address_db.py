#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
郵便番号データベースから住所情報を抽出するスクリプト 📮
括弧内の情報を除去し、都道府県・市区町村名をまとめて重複を除去します
"""

import csv
import re
import argparse
import sys

def clean_address(address):
    """住所から括弧内の情報を除去し、正規化する"""
    if not address:
        return ""
    
    # 括弧内の情報を除去（全角・半角両方対応）
    address = re.sub(r'[（(].*?[）)]', '', address)
    
    # 「以下に掲載がない場合」を除去
    address = address.replace('以下に掲載がない場合', '')
    
    # 余分な空白を除去
    address = address.strip()
    
    return address

def extract_addresses_from_ken_all(input_file, output_file = "/tmp/address_validation_db.csv"):
    """郵便番号データベースから住所情報を抽出"""
    addresses = set()  # 重複を自動的に除去するためsetを使用
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:  # 郵便番号DBはUTF-8
            reader = csv.reader(f)
            
            for row_num, row in enumerate(reader, 1):
                if len(row) < 8:  # 郵便番号DBの最小列数チェック
                    continue
                
                # 漢字の都道府県名（7列目）
                prefecture = clean_address(row[6]) if len(row) > 6 else ""
                
                # 漢字の市区町村名（8列目）
                city = clean_address(row[7]) if len(row) > 7 else ""
                
                # 漢字の町村名（9列目）
                town = clean_address(row[8]) if len(row) > 8 else ""
                
                # 住所を組み立て
                if prefecture and city:
                    if town:
                        full_address = f"{prefecture}{city}{town}"
                    else:
                        full_address = f"{prefecture}{city}"
                    
                    # 空文字でない場合のみ追加
                    if full_address.strip():
                        addresses.add(full_address)
                
                # 進捗表示（1000行ごと）
                if row_num % 1000 == 0:
                    print(f"📊 {row_num}行目を処理中... 現在{len(addresses)}件の住所を抽出済み")
    
    except FileNotFoundError:
        print(f"❌ エラー: ファイル '{input_file}' が見つかりません")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラー: ファイル読み込みに失敗しました: {e}")
        sys.exit(1)
    
    return sorted(list(addresses))  # ソートして返す

def save_addresses_to_csv(addresses, output_file):
    """住所リストをCSVファイルに保存"""
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['住所'])  # ヘッダー
            
            for address in addresses:
                writer.writerow([address])
        
        print(f"✅ {len(addresses)}件の住所を '{output_file}' に保存しました")
        
    except Exception as e:
        print(f"❌ エラー: ファイル保存に失敗しました: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='郵便番号データベースから住所情報を抽出')
    parser.add_argument('input', help='入力ファイル（utf_ken_all.csv）')
    parser.add_argument('-o', '--output', default='address_validation_db.csv', 
                       help='出力CSVファイル名（デフォルト: address_validation_db.csv）')
    parser.add_argument('--show-stats', action='store_true', 
                       help='統計情報を表示')
    
    args = parser.parse_args()
    
    print(f"🔍 郵便番号データベースから住所情報を抽出中...")
    print(f"📁 入力ファイル: {args.input}")
    print(f"📁 出力ファイル: {args.output}")
    print()
    
    # 住所情報を抽出
    addresses = extract_addresses_from_ken_all(args.input)
    
    # 結果を保存
    save_addresses_to_csv(addresses, args.output)
    
    # 統計情報を表示
    if args.show_stats:
        print()
        print("📊 統計情報:")
        print(f"   📍 抽出された住所数: {len(addresses):,}件")
        
        # 都道府県別の統計
        prefecture_counts = {}
        for address in addresses:
            # 都道府県名を抽出（最初の2文字で判定）
            if len(address) >= 2:
                prefecture = address[:2]
                prefecture_counts[prefecture] = prefecture_counts.get(prefecture, 0) + 1
        
        print(f"   🏛️  都道府県数: {len(prefecture_counts)}")
        
        # 上位5件の都道府県を表示
        top_prefectures = sorted(prefecture_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        print("   📈 住所数上位の都道府県:")
        for prefecture, count in top_prefectures:
            print(f"      {prefecture}: {count:,}件")
    
    print()
    print("🎉 処理完了！")

if __name__ == "__main__":
    main() 