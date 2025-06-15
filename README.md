# geo_normalize_csv

自治体が提供するポスター掲示場情報のCSVを正規化し、Google Maps API を使って緯度経度を付与するバッチ処理ツールです。  
CSV形式で複数行の住所データを一括変換し、別の「正規化済みCSV」として出力します。

---

## 🚀 機能概要

- 指定フォーマットに従って **CSVを整形出力**
- Google Maps Geocoding API を使って **緯度・経度を取得**
- JSON形式の設定ファイルで柔軟に制御可能
- 住所に含まれる **漢数字（例：二丁目）をアラビア数字（2丁目）に変換(デフォルトでは変換無し)**

---

## 📦 ディレクトリ構成

```
geo_normalize_csv/
├── geo_normalize_csv.py       # メインスクリプト
├── README.md
└── sample/
    ├── 中央区.csv              # 入力CSV（例）
    ├── 中央区.json            # 設定ファイル
    └── 中央区_normalized.csv  # 出力結果
```

---

## 📄 JSON設定ファイル形式

```json
{
  "input": "./sample/中央区.csv",
  "output": "./sample/中央区_normalized.csv",
  "api": {
    "key": "YOUR_GOOGLE_API_KEY",
    "sleep": 200
  },
  "format": {
    "prefecture": "東京都",
    "city": "中央区",
    "number": "{2}-{3}",
    "address": "{4}",
    "name": "{5}",
    "lat": "{lat}",
    "long": "{long}"
  }
}
```

- `{n}`: 入力CSVの n 列目（1始まり）を参照  
- `{lat}`, `{long}`: Google Maps API から取得される緯度・経度

---

## 🛠️ 使い方

### 1. 必要ライブラリをインストール

```bash
pip install requests
```

### 2. スクリプトを実行

```bash
python geo_normalize_csv.py sample/中央区.json
```

---

## 📌 注意点

- Google Maps Geocoding API を利用するために **APIキーが必要** です  
- APIキーは課金対象になるため、使用量制限などを設定してください  
- `normalize_address_digits` を `true` に設定すると、**漢数字がアラビア数字に変換されます**

---

## 🧪 開発者向け補足

- `{2}-{3}` などのように複数列を組み合わせて1項目を作ることが可能です
- トークン `{lat}`, `{long}` は初回のみ API に問い合わせ、キャッシュされます

---

## 📜 ライセンス

MIT License