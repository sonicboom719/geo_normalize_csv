
# geo_normalize_csv

自治体が提供するポスター掲示場情報のCSVを正規化し、Google Maps APIや国土地理院APIを使って緯度経度を付与するバッチ処理ツールです。  
CSV形式で複数行の住所データを一括変換し、別の「正規化済みCSV」として出力します。
APIで取得した緯度経度が怪しい場合は、出力CSVのnote列に「緯度経度は怪しい」と追記します。

---

## 🚀 機能概要

- 指定フォーマットに従って **CSVを整形出力**
- Google Maps Geocoding API および **国土地理院API** を使って **緯度・経度を取得**
- **2重チェック機能**：両APIの緯度・経度を比較し、ズレが大きい場合は指定した優先APIの値を採用可能
- **逆引きチェック機能**：逆ジオコーディングAPIを使って緯度経度が怪しい場合は国土地理院APIを採用します。
- 上記チェック機能のどちらか1つを選べます。
- チェック機能で引っかかった場合は、出力CSVのnote列に「緯度経度は怪しい」を追記
- デフォルトでは「2重チェック機能」が動作します。「逆ジオコーディングチェック機能」を使う場合はJSON設定します。
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
    "sleep": 200,
    "gsi_check": {
      "check": true,
      "distance": 200,
      "priority": "gsi"
    },
    "reverse_geocode_check": true,   // 逆ジオコーディングチェック有効化
    "mode": "reverse_geocode"        // 逆引きチェックする場合はreverse_geocodeに、2つのAPIの距離差でチェックする場合はdistanceに指定
  },
  },
  "format": {
    "prefecture": "東京都",
    "city": "中央区",
    "number": "{2}-{3}",
    "address": "{4}",
    "name": "{5}",
    "lat": "{lat}",
    "long": "{long}"
    "note": ""
  }
}
```
- `{n}`: 入力CSVの n 列目（1始まり）を参照  
- `{lat}`, `{long}`: APIから取得される緯度・経度

---

### 🏛️ **国土地理院APIによる2重チェック機能（gsi_check）について**

#### `api.gsi_check` 設定例

```json
"gsi_check": {
  "check": true,
  "distance": 200,
  "priority": "gsi"
}
```

| パラメータ名 | 型      | 説明 |
|--------------|---------|--------------------------------------------------------------------|
| check        | boolean | `true`なら2重チェックを有効にします。Googleと国土地理院APIで距離差を比較 |
| distance     | int     | 距離閾値（メートル）。この値以上のズレがあればpriority設定に従い優先APIを決定 |
| priority     | string  | `"gsi"`なら国土地理院API、`"google"`ならGoogleの値をズレ時に採用<br>省略時は"gsi" |

- **check**  
  `true` なら、Google APIと国土地理院APIの両方から座標を取得し「ズレ（距離差）」を比較します。
- **distance**  
  両APIの座標の距離差（メートル）を指定。この値以上のズレがあれば、下記priority設定に従い、どちらかのAPIの値を「採用値」としてCSV出力します。
- **priority**  
  `"gsi"`の場合…ズレがdistance以上なら**国土地理院API**の座標を優先  
  `"google"`の場合…ズレがdistance以上なら**Google Maps API**の座標を優先  
  他の値の場合はエラーで終了します。  
  **省略時・無指定時は"gsi"（国土地理院API優先）がデフォルトとなります。**

> **おすすめ**：  
> 国土地理院APIの精度が高いため、`priority: "gsi"`（デフォルト）のままがおすすめです。

---

### 📝 **設定の解説**
- `gsi_check`自体や各項目が未指定の場合は「200m以上ズレは国土地理院API採用」のデフォルトとなります
- `priority`は `"gsi"`または`"google"`のみ指定可能
- **ズレがdistance未満の場合はGoogleの座標を採用します**

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
- 国土地理院APIで座標が取得できない場合や設定エラー時は適宜警告メッセージが出ます

---

## 🧪 開発者向け補足

- `{2}-{3}` などのように複数列を組み合わせて1項目を作ることが可能です
- トークン `{lat}`, `{long}` は初回のみ API に問い合わせ、キャッシュされます
- 両APIの差分チェックや出力値カスタマイズも可能です

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

## 📜 ライセンス

MIT License
