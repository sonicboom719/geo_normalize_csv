# 📝 Loggingシステムの使用方法

## 🎯 概要

`map_extensions_osmnx.py`では、print文をloggingシステムに置き換えて、ログレベルによる出力制御を実装しました。

## 🔧 ログレベルの設定

### 環境変数による設定

```bash
# DEBUGレベル（全てのログを表示）
export LOG_LEVEL=DEBUG
python map_extensions_osmnx.py

# INFOレベル（通常の実行情報のみ）
export LOG_LEVEL=INFO
python map_extensions_osmnx.py

# WARNINGレベル（警告とエラーのみ）
export LOG_LEVEL=WARNING
python map_extensions_osmnx.py

# ERRORレベル（エラーのみ）
export LOG_LEVEL=ERROR
python map_extensions_osmnx.py
```

### デフォルト設定

環境変数が設定されていない場合、デフォルトで`INFO`レベルが使用されます。

## 📊 ログレベルの詳細

### DEBUG
- **用途**: デバッグ用の詳細情報
- **内容**: 
  - 座標計算の詳細
  - 垂直投影の計算過程
  - ポリゴン辺の特定過程
  - 回転角度の計算
- **表示例**:
  ```
  🔍 角の確認: NE=(139.406624, 35.651699), NW=(139.394825, 35.651750)
  🔍 垂直投影デバッグ: 角1=(139.406624, 35.651699), 角2=(139.405812, 35.649905), 方向=east
  ```

### INFO
- **用途**: 通常の実行情報
- **内容**:
  - 処理の開始・完了
  - 座標取得の成功
  - 可視化結果の保存
  - 方向別座標の計算結果
- **表示例**:
  ```
  🌐 場所 '多摩動物園, 日野市, 日本' のデータをosmnxから取得中...
  ✅ 場所 '多摩動物園, 日野市, 日本' のデータを正常に取得しました
  📍 東側の辺上位置座標: 経度=139.406218, 緯度=35.650802
  ```

### WARNING
- **用途**: 警告情報
- **内容**:
  - 代替アルゴリズムの使用
  - 期待しない動作の検出
  - フォールバック処理の実行
- **表示例**:
  ```
  ⚠️ ポリゴン上に指定された点が見つかりませんでした: point1_idx=-1, point2_idx=-1
  🔍 交点なし、別の方法を試行...
  🔍 代替点も見つからず、中点を使用: (139.400725, 35.652556)
  ```

### ERROR
- **用途**: エラー情報
- **内容**:
  - 処理の失敗
  - データ取得エラー
  - 座標計算エラー
- **表示例**:
  ```
  ❌ 場所 '存在しない場所' が見つかりませんでした
  ❌ GeoDataFrameが空です
  ❌ 座標計算中にエラーが発生しました: division by zero
  ```

## 📁 ログファイル

### ファイル出力
- **ファイル名**: `map_extensions_osmnx.log`
- **エンコーディング**: UTF-8
- **ログレベル**: DEBUG（全てのログを記録）
- **フォーマット**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

### ログファイルの例
```
2025-01-27 10:30:15 - __main__ - INFO - 🌐 場所 '多摩動物園, 日野市, 日本' のデータをosmnxから取得中...
2025-01-27 10:30:16 - __main__ - INFO - ✅ 場所 '多摩動物園, 日野市, 日本' のデータを正常に取得しました
2025-01-27 10:30:16 - __main__ - DEBUG - 🔍 角の確認: NE=(139.406624, 35.651699), NW=(139.394825, 35.651750)
2025-01-27 10:30:16 - __main__ - DEBUG - 🔍 垂直投影デバッグ: 角1=(139.406624, 35.651699), 角2=(139.405812, 35.649905), 方向=east
2025-01-27 10:30:16 - __main__ - INFO - 📍 東側の辺上位置座標: 経度=139.406218, 緯度=35.650802
```

## 🎨 使用例

### 開発・デバッグ時
```bash
# 全てのログを表示してデバッグ
export LOG_LEVEL=DEBUG
python map_extensions_osmnx.py
```

### 通常実行時
```bash
# 重要な情報のみ表示
export LOG_LEVEL=INFO
python map_extensions_osmnx.py
```

### 本番環境
```bash
# エラーのみ表示
export LOG_LEVEL=ERROR
python map_extensions_osmnx.py
```

### ログファイルの確認
```bash
# ログファイルの内容を確認
tail -f map_extensions_osmnx.log

# エラーログのみを確認
grep "ERROR" map_extensions_osmnx.log

# デバッグログのみを確認
grep "DEBUG" map_extensions_osmnx.log
```

## 🔄 ログレベルの変更方法

### プログラム内での変更
```python
import logging
logger = logging.getLogger(__name__)

# ログレベルを動的に変更
logger.setLevel(logging.DEBUG)  # デバッグレベルに変更
logger.setLevel(logging.INFO)   # 情報レベルに変更
logger.setLevel(logging.WARNING) # 警告レベルに変更
logger.setLevel(logging.ERROR)  # エラーレベルに変更
```

### 環境変数での変更
```bash
# 一時的な変更
LOG_LEVEL=DEBUG python map_extensions_osmnx.py

# 永続的な変更
echo 'export LOG_LEVEL=INFO' >> ~/.bashrc
source ~/.bashrc
```

## 💡 ベストプラクティス

1. **開発時**: `DEBUG`レベルを使用して詳細な情報を確認
2. **テスト時**: `INFO`レベルで正常動作を確認
3. **本番環境**: `WARNING`または`ERROR`レベルで必要最小限のログのみ表示
4. **ログファイル**: 常に`DEBUG`レベルで全てのログを記録し、後から分析可能にする

## 🐛 トラブルシューティング

### ログが表示されない場合
```bash
# ログレベルを確認
echo $LOG_LEVEL

# デフォルトレベルで実行
unset LOG_LEVEL
python map_extensions_osmnx.py
```

### ログファイルが作成されない場合
```bash
# ファイルの書き込み権限を確認
ls -la map_extensions_osmnx.log

# ディレクトリの書き込み権限を確認
ls -la .
```

### ログレベルが反映されない場合
```bash
# 環境変数を再設定
export LOG_LEVEL=DEBUG
python map_extensions_osmnx.py
```

## 📚 関連ファイル

- `map_extensions_osmnx.py`: メインのPythonファイル
- `map_extensions_osmnx.log`: ログファイル（実行時に自動生成）
- `README.md`: プロジェクトの概要
- `README_DIRECTION_MARKERS.md`: 方向マーカーの仕様

---

🎉 **ログシステムにより、デバッグと本番環境での運用が大幅に改善されました！** 