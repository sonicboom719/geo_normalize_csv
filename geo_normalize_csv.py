import csv
import json
import sys
import time
import requests
import unicodedata
import re

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
    def replacer(match):
        kanji = match.group(1)
        unit = match.group(2)
        return f"{kanji_to_number(kanji)}{unit}"
    return re.sub(r"([〇一二三四五六七八九十]+)(丁目|番|号)", replacer, addr).strip().strip("　")

def clean(val):
    return val.strip().strip("　") if isinstance(val, str) else val

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def read_csv(path):
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        return list(reader)[1:]

def get_lat_lng(address, api_key):
    print(f"Geocode APIコール中です: {address}")
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}
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
            return f"ERROR:{status}", f"ERROR:{status}"
    except Exception as e:
        return f"ERROR:{str(e)}", f"ERROR:{str(e)}"

def render_template(template_str, row, cache, full_api_address, api_key, sleep_msec):
    def replacer(match):
        token = match.group(1)
        if token.isdigit():
            idx = int(token) - 1
            return clean(row[idx]) if idx < len(row) else ""
        elif token in ("lat", "long"):
            if "latlng" not in cache:
                lat, lng = get_lat_lng(full_api_address, api_key)
                cache["latlng"] = (lat, lng)
                time.sleep(sleep_msec / 1000)
            lat, lng = cache["latlng"]
            return str(clean(lat if token == "lat" else lng))
        else:
            return ""
    return re.sub(r"\{([^{}]+)\}", replacer, template_str)

def process(config_path):
    config = load_config(config_path)
    input_rows = read_csv(config["input"])
    format_config = config["format"]
    header = list(format_config.keys())
    output_path = config["output"]

    api_needed = any("{lat}" in v or "{long}" in v for v in format_config.values())
    api_key = config.get("api", {}).get("key") if api_needed else None
    sleep_msec = int(config.get("api", {}).get("sleep", 200)) if api_needed else 200

    if api_needed and not api_key:
        raise ValueError("緯度経度を取得するにはAPIキーが必要です。")

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        csv.writer(f).writerow(header)

    for idx, row in enumerate(input_rows, start=1):
        print(f"{idx}行目を処理中です")
        out_row = []
        cache = {}

        # 元の住所列のインデックスを取得
        address_token = format_config.get("address", "")
        if "{" in address_token and "}" in address_token:
            match = re.search(r"\{(\d+)\}", address_token)
            address_index = int(match.group(1)) - 1 if match else -1
            raw_address = row[address_index] if 0 <= address_index < len(row) else ""
        else:
            raw_address = ""

        if config.get("normalize_address_digits", False):
            normalized_address = normalize_address_digits(raw_address)
        else:
            normalized_address = raw_address.strip().strip("　")

        full_api_address = f"{format_config['prefecture']}{format_config['city']}{normalized_address}"

        for col_name, template in format_config.items():
            if col_name == "address":
                out_row.append(clean(normalized_address))
            else:
                rendered = render_template(template, row, cache, full_api_address, api_key, sleep_msec)
                out_row.append(rendered)

        with open(output_path, 'a', encoding='utf-8', newline='') as f:
            csv.writer(f).writerow(out_row)

    print(f"\n完了：{len(input_rows)}件のデータを出力しました → {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python geo_normalize.py <config.json>")
        sys.exit(1)
    process(sys.argv[1])
