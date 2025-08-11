import csv
import json
import sys
import time
import requests
import unicodedata
import re
from math import radians, cos, sin, sqrt, atan2
import percache, os
from pathlib import Path  # パス操作用
from dotenv import load_dotenv  # .envファイル読み込み用

# .envファイルを自動的に読み込み 🔄
load_dotenv()

# macOS標準的なキャッシュディレクトリを使用 🍎
CACHE_DIR = Path.home() / "Library" / "Caches" / "geo_normalize_csv"
CACHE_DIR.mkdir(parents=True, exist_ok=True)  # ディレクトリが存在しない場合は作成
CACHE_FILE = str(CACHE_DIR / "geo_cache")  # .db拡張子を追加
geoCache = percache.Cache(CACHE_FILE)

KANJI_NUMERAL_MAP = {
    "〇": 0, "一": 1, "二": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
    "十": 10
}

def kanji_to_number(kanji):
    if kanji == "十":
        return 10
    if "十" in kanji:
        parts = kanji.split("十")
        left = KANJI_NUMERAL_MAP.get(parts[0], 1) if parts[0] else 1
        right = KANJI_NUMERAL_MAP.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
        return left * 10 + right
    num = 0
    for ch in kanji:
        num = num * 10 + KANJI_NUMERAL_MAP.get(ch, 0)
    return num

def normalize_address_digits(addr):
    addr = unicodedata.normalize("NFKC", addr)
    addr = re.sub(r"[‐－―ー−]", "-", addr)
    
    # 漢数字の処理
    def replacer(match):
        kanji = match.group(1)
        unit = match.group(2)
        return f"{kanji_to_number(kanji)}{unit}"
    addr = re.sub(r"([〇一二三四五六七八九十]+)(丁目|番|号)", replacer, addr)
    
    # アラビア数字のハイフンパターン処理（1-29 → 1丁目29番）
    def arabic_replacer(match):
        num1 = match.group(1)
        num2 = match.group(2)
        return f"{num1}丁目{num2}番"
    addr = re.sub(r"(\d+)-(\d+)", arabic_replacer, addr)
    
    return addr.strip().strip("　")

def clean(val):
    return val.strip().strip("　") if isinstance(val, str) else val

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_api_key_from_env():
    """環境変数からGoogle APIキーを取得する関数 🔑"""
    return os.getenv('GOOGLE_API_KEY') or os.getenv('GOOGLE_MAPS_API_KEY')

def get_api_key_with_fallback(config):
    """JSON設定からAPIキーを取得し、ない場合は.envファイルから取得する関数 🔄"""
    # JSON設定からAPIキーを取得
    api_key = get_api_key_from_env()
    
    # .envにAPIキーが定義されていない場合、JSONファイルから取得
    if not api_key:
        api_key = config.get("api", {}).get("key")
        if api_key:
            print("📝 .envにAPIキーが定義されていないため、JSONファイルから読み込みました")
        else:
            print("⚠️  JSON設定と.envファイルの両方にAPIキーが定義されていません")
    
    return api_key

def read_csv(path):
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        return list(reader)[1:]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))

@geoCache  # Google Maps API呼び出しをキャッシュ 💾
def get_gmap_latlng(address, api_key):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key, "language": "ja"}
    try:
        res = requests.get(url, params=params)
        data = res.json()
        status = data.get("status")
        if status == "OK":
            loc = data["results"][0]["geometry"]["location"]
            return loc["lat"], loc["lng"]
        elif status == "REQUEST_DENIED":
            print(f"認証エラー: {data.get('error_message', 'APIキーが無効です。')}")
            sys.exit(1)
        else:
            return None, None
    except Exception as e:
        return None, None

@geoCache  # 国土地理院API呼び出しをキャッシュ 💾
def get_gsi_latlng(address):
    url = "https://msearch.gsi.go.jp/address-search/AddressSearch"
    params = {"q": address}
    try:
        res = requests.get(url, params=params)
        result = res.json()
        if result and "geometry" in result[0]:
            lon, lat = result[0]["geometry"]["coordinates"]
            return lat, lon
        return None, None
    except Exception:
        return None, None

@geoCache  # Google逆ジオコーディングAPI呼び出しをキャッシュ 💾
def reverse_geocode_google(lat, lng, api_key):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"latlng": f"{lat},{lng}", "key": api_key, "language": "ja"}
    try:
        res = requests.get(url, params=params)
        data = res.json()
        if data.get("status") == "OK":
            return data["results"][0]["formatted_address"]
        else:
            return None
    except Exception:
        return None

def normalize_japanese_address(addr):
    if not addr:
        return ""
    addr = unicodedata.normalize("NFKC", addr)
    addr = re.sub(r'日本|JAPAN', '', addr, flags=re.IGNORECASE)
    addr = re.sub(r'〒\d{3}-?\d{4}', '', addr)
    addr = re.sub(r'^[\s、,．.]+', '', addr)
    addr = re.sub(r'\s+', '', addr)
    addr = re.sub(r'[‐－―ー−]', '-', addr)
    addr = addr.replace('番地', '番')
    addr = normalize_address_digits(addr)
    addr = re.sub(r'(先|付近|階|Ｆ|号室|室|[A-Za-zａ-ｚＡ-Ｚ]{1,10})$', '', addr)

    # 丁目を-に変換
    addr = re.sub(r'丁目', '-', addr)
    
    # 番を-に変換
    addr = re.sub(r'番', '-', addr)
    
    # 号を-に変換
    addr = re.sub(r'号', '-', addr)
    
    # 余分なハイフンを削除（連続するハイフンを1つに）
    addr = re.sub(r'-+', '-', addr)
    
    # 最後の余分なハイフンを削除
    addr = re.sub(r'-+$', '', addr)
    
    # 全角数字を半角数字に変換
    addr = addr.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
    
    return addr

def addresses_roughly_match(addr1, addr2, threshold=None):
    import re
    print(f"addr1={addr1} addr2={addr2}")
    core1 = normalize_japanese_address(addr1)
    core2 = normalize_japanese_address(addr2)
    
    # core2から最後の施設名部分を削除（-で区切られた最後の部分が施設名の場合）
    if '-' in core2:
        parts = core2.split('-')
        # 最後の部分が数字でない場合は施設名として削除
        if parts and not parts[-1].isdigit():
            core2 = '-'.join(parts[:-1])
    
    # core1のハイフン数に合わせてcore2を調整
    core1_hyphen_count = core1.count('-')
    core2_hyphen_count = core2.count('-')
    
    if core2_hyphen_count > core1_hyphen_count:
        # core2のハイフンが多い場合、core1のハイフン数に合わせて切り詰める
        parts = core2.split('-')
        # core1のハイフン数+1の部分までを保持（例：core1が2個のハイフンなら3個の部分まで）
        adjusted_parts = parts[:core1_hyphen_count + 1]
        core2 = '-'.join(adjusted_parts)
        #print(f"core2を調整: ハイフン数 {core2_hyphen_count} → {core1_hyphen_count}")
    
    #print(f"core1={core1} core2={core2}")
    return core1 == core2

def get_best_latlng(address, api_key, gsi_check=True, distance_threshold=200, priority="gsi",
                    mode="distance", reverse_geocode_check=False, note_out=None):
    lat1, lon1 = get_gmap_latlng(address, api_key)
    lat2, lon2 = get_gsi_latlng(address)

    if lat1 is None and lat2 is None:
        print(f"警告: '{address}' の座標取得に失敗しました。")
        if note_out is not None:
            note_out.append("緯度経度は怪しい")
        return None, None, "none"

    # 逆ジオコーディングモード
    if mode == "reverse_geocode" and reverse_geocode_check and lat1 is not None:
        rev_addr = reverse_geocode_google(lat1, lon1, api_key)
        suspicious = False
        if rev_addr is not None:
            if not addresses_roughly_match(address, rev_addr):
                print(f"警告: '{address}' Google座標の逆引きが不一致'{rev_addr}' → 国土地理院APIを採用します。")
                suspicious = True
        else:
            suspicious = True  # 逆ジオコーディング失敗も怪しいとみなす
        if suspicious:
            if note_out is not None:
                note_out.append("緯度経度は怪しい")
            if lat2 is not None:
                return lat2, lon2, "gsi"
            else:
                return None, None, "none"
        else:
            return lat1, lon1, "google"

    # 距離チェックモード（従来方式）
    if mode == "distance":
        if lat1 is not None and lat2 is None:
            return lat1, lon1, "google"
        if lat2 is not None and lat1 is None:
            return lat2, lon2, "gsi"
        dist = haversine(lat1, lon1, lat2, lon2)
        if gsi_check and dist >= distance_threshold:
            print(f"警告: '{address}' のGoogle座標と国土地理院座標が {int(dist)}m ズレ。", end="")
            if note_out is not None:
                note_out.append("緯度経度は怪しい")
            if priority == "gsi":
                print("国土地理院APIの座標を採用します。")
                return lat2, lon2, "gsi"
            elif priority == "google":
                print("Google座標を採用します。")
                return lat1, lon1, "google"
            else:
                print(f"\nエラー: api.gsi_check.priorityの値 '{priority}' はサポートされていません。'gsi'または'google'のみ指定可能です。")
                sys.exit(1)
        return lat1, lon1, "google"

    if lat1 is not None:
        return lat1, lon1, "google"
    if lat2 is not None:
        return lat2, lon2, "gsi"
    if note_out is not None:
        note_out.append("緯度経度は怪しい")
    return None, None, "none"

def render_template(template_str, row, cache, full_api_address, api_key, sleep_msec,
                    gsi_check, gsi_dist, priority, mode, reverse_geocode_check):
    def replacer(match):
        token = match.group(1)
        if token.isdigit():
            idx = int(token) - 1
            return clean(row[idx]) if idx < len(row) else ""
        elif token in ("lat", "long"):
            if "latlng" not in cache:
                # lat, lng をキャッシュ
                # note_outはここでは使わない（get_best_latlngはprocessで実行）
                pass
            lat, lng = cache.get("latlng", (None, None))
            return str(clean(lat if token == "lat" else lng))
        else:
            return ""
    return re.sub(r"\{([^{}]+)\}", replacer, template_str)

def remove_street_number(address):
    # 「先」「外」「東西南北」で終わる住所の場合、「先」「外」「東西南北」を削除 🔧
    if address.endswith('先') or address.endswith('外') or address.endswith('東') or address.endswith('西') or address.endswith('南') or address.endswith('北'):
        address = address[:-1]  # 最後の「先」を削除

    """住所から番地部分を取り除く"""
    # 番地パターンを削除（例: 1-2-3, 123, 1丁目2番3号など）
    address = re.sub(r'[0-9０-９]+[-－][0-9０-９]+[-－]?[0-9０-９]*', '', address)
    address = re.sub(r'[0-9０-９]+丁目[0-9０-９]+番[0-9０-９]*号?', '', address)
    address = re.sub(r'[0-9０-９]+番[0-9０-９]*号?', '', address)
    address = re.sub(r'[0-9０-９]+丁目', '', address)
    address = re.sub(r'[0-9０-９]+番', '', address)
    address = re.sub(r'[0-9０-９]+号', '', address)
    address = re.sub(r'[0-9０-９]+$', '', address)

    return address.strip()

def calculate_similarity(str1, str2):
    """文字列の類似度を計算（レーベンシュタイン距離ベース）"""
    if not str1 or not str2:
        return 0
    
    # 文字列を正規化
    str1 = str1.replace('ヶ', 'ケ').replace('が', 'ガ')
    str2 = str2.replace('ヶ', 'ケ').replace('が', 'ガ')
    
    # レーベンシュタイン距離を計算
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    distance = levenshtein_distance(str1, str2)
    max_len = max(len(str1), len(str2))
    similarity = 1 - (distance / max_len) if max_len > 0 else 0
    return similarity

def find_similar_addresses(target_address, validation_db, max_suggestions=3, similarity_threshold=0.3):
    """類似住所を検索して提案する"""
    if not validation_db:
        return []
    
    # 番地部分を取り除いて正規化
    normalized_target = remove_street_number(target_address)
    
    # 類似度を計算してソート
    similarities = []
    for db_address in validation_db:
        normalized_db = remove_street_number(db_address)
        similarity = calculate_similarity(normalized_target, normalized_db)
        if similarity >= similarity_threshold:
            similarities.append((db_address, similarity))
    
    # 類似度でソートして上位を返す
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:max_suggestions]

def load_address_validation_db(db_path):
    """住所検証用DBを読み込む"""
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            addresses = set()
            for row in reader:
                address = row[0].strip() if row else ""
                if address:
                    addresses.add(address)
        print(f"✅ 住所検証DBを読み込みました: {len(addresses)}件 (ファイル: {os.path.abspath(db_path)})")
        return addresses
    except FileNotFoundError:
        print(f"⚠️  警告: 住所検証DB '{db_path}' が見つかりません")
        return set()
    except Exception as e:
        print(f"❌ エラー: 住所検証DBの読み込みに失敗しました: {e}")
        return set()

def validate_address(address, validation_db, high_similarity_threshold=0.8):
    """住所の実在性をチェックし、高確率の類似住所があれば採用する"""
    if not validation_db:
        return True, "住所検証DBが利用できません", None
    
    # 番地部分を取り除いて住所を正規化
    normalized_address = remove_street_number(address)
    
    # デバッグ情報（必要に応じてコメントアウト） 🔍
    # print(f"🔍 住所検証デバッグ:")
    # print(f"  元の住所: '{address}'")
    # print(f"  正規化後: '{normalized_address}'")
    # print(f"  DBに存在: {normalized_address in validation_db}")
    
    # 住所DBに存在するかチェック
    if normalized_address in validation_db:
        return True, f"住所が確認されました: {normalized_address}", None
    else:
        # 類似住所を検索して提案
        similar_addresses = find_similar_addresses(address, validation_db, max_suggestions=5, similarity_threshold=0.3)
        
        # 高確率の類似住所をチェック（閾値0.8以上）
        high_similarity_address = None
        if similar_addresses and similar_addresses[0][1] >= high_similarity_threshold:
            if similar_addresses[0][0] in validation_db:
                high_similarity_address = similar_addresses[0][0]  # 最も類似度の高い住所を採用
                print(f"🎯 高確率類似住所を採用: '{address}' → '{high_similarity_address}' (類似度: {similar_addresses[0][1]:.2f})")
        
        suggestion_text = ""
        if similar_addresses:
            suggestion_text = " 類似住所候補: " + ", ".join([f"{addr} ({sim:.1f})" for addr, sim in similar_addresses])
        
        if high_similarity_address:
            return True, f"高確率類似住所を採用: {high_similarity_address} (元: {normalized_address})", high_similarity_address
        else:
            return False, f"住所が見つかりません: {normalized_address}{suggestion_text}", None

def process(config_path):
    config = load_config(config_path)
    input_rows = read_csv(config["input"])
    format_config = config["format"]
    header = list(format_config.keys())
    if "note" not in header:
        header.append("note")
    output_path = config["output"]

    api_needed = any("{lat}" in v or "{long}" in v for v in format_config.values())
    # APIキー取得を新しい関数に変更 🔄
    api_key = get_api_key_with_fallback(config) if api_needed else None
    sleep_msec = int(config.get("api", {}).get("sleep", 200)) if api_needed else 200

    # 住所検証DBの読み込み
    validation_db_path = config.get("address_validation_db", "/tmp/address_validation_db.csv")  # デフォルト設定を/tmp/address_validation_db.csvに変更
    if validation_db_path == "":
        validation_db_path = "/tmp/address_validation_db.csv"
    validation_db = load_address_validation_db(validation_db_path)

    api_opts = config.get("api", {})
    mode = api_opts.get("mode", "distance")
    reverse_geocode_check = bool(api_opts.get("reverse_geocode_check", False))

    gsi_opts = api_opts.get("gsi_check", None)
    if gsi_opts is None:
        gsi_check = True
        gsi_dist = 200
        priority = "gsi"
    else:
        gsi_check = bool(gsi_opts.get("check", True))
        gsi_dist = int(gsi_opts.get("distance", 200))
        priority = gsi_opts.get("priority", "gsi")
        if priority not in ("gsi", "google"):
            print(f"\nエラー: api.gsi_check.priorityの値 '{priority}' はサポートされていません。'gsi'または'google'のみ指定可能です。")
            sys.exit(1)

    if api_needed and not api_key:
        raise ValueError("緯度経度を取得するにはAPIキーが必要です。")

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        csv.writer(f).writerow(header)

    for idx, row in enumerate(input_rows, start=1):
        out_row = []
        cache = {}
        note_list = []

        # address列の作成部分
        address_token = format_config.get("address", "")
        if "{" in address_token and "}" in address_token:
            match = re.search(r"\{(\d+)\}", address_token)
            address_index = int(match.group(1)) - 1 if match else -1
            raw_address = row[address_index] if 0 <= address_index < len(row) else ""
        else:
            raw_address = ""

        # 不要な空白' 'を削除（後処理への影響を防ぐ） 🗑️
        raw_address = raw_address.replace(' ', '')

        if config.get("normalize_address_digits", False):
            normalized_address = normalize_address_digits(raw_address)
        else:
            normalized_address = raw_address.strip().strip("　")

        # normalized_addressに既に都道府県名や市町村名が含まれているかチェック 🔍
        prefecture = format_config['prefecture']
        city = format_config['city']
        
        # 都道府県名と市町村名の両方が行頭から含まれている場合
        if normalized_address.startswith(prefecture + city):
            # 行頭の都道府県名と市町村名を取り除く
            normalized_address = normalized_address[len(prefecture + city):]
        # 市町村名が行頭から含まれている場合
        elif normalized_address.startswith(city):
            # 行頭の市町村名を取り除く
            normalized_address = normalized_address[len(city):]
        # 都道府県名が行頭から含まれている場合
        elif normalized_address.startswith(prefecture):
            # 行頭の都道府県名を取り除く
            normalized_address = normalized_address[len(prefecture):]
        
        # 「ヶ」を「ケ」に置換したバージョンも生成 🔄
        original_address = normalized_address
        ke_replaced_address = normalized_address.replace('ヶ', 'ケ')
        
        # 元の住所と「ケ」置換版の両方を処理
        addresses_to_process = []
        if original_address != ke_replaced_address:
            addresses_to_process.append((original_address, "original"))
            addresses_to_process.append((ke_replaced_address, "ke_replaced"))
        else:
            addresses_to_process.append((original_address, "original"))
        
        for address_variant, variant_type in addresses_to_process:
            full_api_address = f"{prefecture}{city}{address_variant}"
            
            print(f"{idx}行目を処理中です: {full_api_address}")
            
            # 区番号を取得
            number_token = format_config.get("number", "")
            if "{" in number_token and "}" in number_token:
                match = re.search(r"\{(\d+)\}", number_token)
                number_index = int(match.group(1)) - 1 if match else -1
                district_number = row[number_index] if 0 <= number_index < len(row) else ""
            else:
                district_number = ""

            # 住所の実在性チェック
            is_valid, validation_message, adopted_address = validate_address(full_api_address, validation_db)
            
            # 高確率の類似住所が採用された場合、full_api_addressを書き換える
            if adopted_address:
                original_address = full_api_address
                full_api_address = adopted_address
                print(f"🔄 住所を書き換えました: '{original_address}' → '{full_api_address}'")
            
            if not is_valid:
                print(f"⚠️  住所エラー (区番号{district_number}, 行{idx}): {validation_message}")
                note_list.append(f"住所エラー: {validation_message}")
                # 座標取得をスキップ
                cache["latlng"] = (None, None)
                cache["source"] = "skipped"
            else:
                # 住所検証（OCR誤字チェック）
                if api_key and config.get("validate_address", False):
                    pass
                
                # 緯度経度（note_listを渡してget_best_latlng内でnote列をセット）
                lat, lng, source = get_best_latlng(
                    full_api_address, api_key, gsi_check, gsi_dist, priority, mode, reverse_geocode_check, note_list
                )
                cache["latlng"] = (lat, lng)
                cache["source"] = source
            
            # 出力行の生成
            out_row = []
            for col_name in header:
                if col_name == "note":
                    variant_note = f"[{variant_type}]" if variant_type != "original" else ""
                    out_row.append("".join(note_list) + variant_note)
                elif col_name == "address":
                    out_row.append(clean(address_variant))
                elif col_name in format_config:
                    rendered = render_template(
                        format_config[col_name], row, cache, full_api_address, api_key, sleep_msec,
                        gsi_check, gsi_dist, priority, mode, reverse_geocode_check
                    )
                    out_row.append(rendered)
                else:
                    out_row.append("")

            with open(output_path, 'a', encoding='utf-8', newline='') as f:
                csv.writer(f).writerow(out_row)

    print(f"\n完了：{len(input_rows)}件のデータを出力しました → {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python geo_normalize_csv.py <config.json>")
        sys.exit(1)
    process(sys.argv[1])
