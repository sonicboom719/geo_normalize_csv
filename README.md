
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
├── cat_normalize_csv.py       # CSV連結ツール（政令指定都市用など）
├── README.md
└── sample/
    ├── 中央区.csv              # 入力CSV（例）
    ├── 中央区.json             # 設定ファイル
    ├── 中央区_normalized.csv   # 出力結果
    ├── さいたま市_normalized.csv         # 各区を連結した市全体の正規化CSV（例）
    ├── さいたま市_normalized_北区.csv    # 各区ごとの正規化CSV（例）
    ├── さいたま市_normalized_西区.csv
    └── さいたま市_normalized_大宮区.csv
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

## 🐱 cat_normalize_csv.py について

政令指定都市（市の中に複数の区がある都市）に対応するため、
**各区ごとに正規化されたCSVファイルを、ひとつの市全体のCSVファイルとして連結**できるツールです。

### 🏙️ 典型的な利用例

1. **区ごとの正規化済みCSVを作る**  
   例：`geo_normalize_csv.py` で
   - `./sample/さいたま市_normalized_北区.csv`
   - `./sample/さいたま市_normalized_西区.csv`
   - `./sample/さいたま市_normalized_大宮区.csv`
   などを作成

2. **cat_normalize_csv.py で連結し、市全体のCSVにまとめる**  
   - 例：`./sample/さいたま市_normalized.csv`

### 📝 使い方

#### 必要ファイル：
- `cat_normalize_csv.py`（このリポジトリに同梱されています）

#### 実行方法：

```bash
python cat_normalize_csv.py ./sample/さいたま市_normalized
```

- `./sample/さいたま市_normalized_*.csv` 形式（`*`には区名が入る）の全てのCSVファイルが連結され、
- 1つの `./sample/さいたま市_normalized.csv` が作成されます。

#### 注意：
- 入力CSVのヘッダは必ず  
  `prefecture,city,number,address,name,lat,long`  
  となっている必要があります（異なる場合はエラーになります）。
- 連結対象は、指定したprefix（例：`./sample/さいたま市_normalized_`）に続く、1文字以上のファイル名＋`.csv` です。
- 連結順はワイルドカード部分（区名）が辞書順になります。

#### 出力例：
```
./sample/さいたま市_normalized_北区.csv: データ行数 185
./sample/さいたま市_normalized_西区.csv: データ行数 140
./sample/さいたま市_normalized_大宮区.csv: データ行数 163
3 個のファイルを ./sample/さいたま市_normalized.csv に連結しました。
```

---

### 🧩 こんなときに便利

- 各区単位で正規化処理を進めたあと、「市」全体のデータが欲しい場合
- 各区の担当者が別々に正規化CSVを作っても、あとから1つにまとめたい場合

---

**本ツールのスクリプトも本リポジトリに同梱されています。  
困った場合は [issues](https://github.com/sonicboom719/geo_normalize_csv/issues) でご質問ください。**

---

## 📜 ライセンス

MIT License
