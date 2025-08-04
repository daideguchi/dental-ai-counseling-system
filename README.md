# Dental Counseling AI System

音声記録からSOAP形式診療記録を自動生成する歯科カウンセリングAIシステム

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

## 概要

PLAUD NOTEやNottaなどの音声記録ツールから出力されたファイルを解析し、歯科診療に特化したSOAP形式の診療記録を自動生成します。プロフェッショナルでフォーマルなUIデザインを採用し、医療現場での使用に適した信頼性の高いシステムです。

## 主な機能

- 🎙️ **複数形式対応**: PLAUD NOTE (TXT/MD/MP3/WAV) および Notta (CSV/XLSX/TXT/SRT/MP3/WAV) に対応
- 🤖 **AI自動解析**: 患者・医師の発言を自動識別し、歯科特有のキーワードを抽出
- 📋 **SOAP形式生成**: 主観的情報(S)、客観的所見(O)、評価(A)、計画(P)を自動生成
- 📊 **品質分析**: コミュニケーション品質、患者理解度、治療同意可能性を数値化
- 💾 **データ管理**: セッション履歴の保存と検索機能
- 🎨 **プロフェッショナルUI**: 医療系に適したフォーマルでシンプルなデザイン

## デモ

[Live Demo](https://yourusername.github.io/dental-counseling-ai/)

## スクリーンショット

<img width="800" alt="メイン画面" src="https://user-images.githubusercontent.com/xxx/xxx.png">

## 技術スタック

- **フロントエンド**: HTML5, CSS3, Vanilla JavaScript
- **バックエンド**: Python 3.8+
- **データベース**: SQLite3
- **AI/ML**: Google Gemini API (オプション)
- **UI**: レスポンシブデザイン、ダークテーマ対応

## インストール

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/dental-counseling-ai.git
cd dental-counseling-ai

# Python仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

## 使用方法

### 1. シンプルなWebUIの起動

```bash
# UIディレクトリに移動
cd ui

# HTTPサーバーの起動
python -m http.server 8000

# ブラウザで開く
# http://localhost:8000
```

### 2. 基本的な使い方

1. PLAUD NOTEまたはNottaから音声記録ファイルをエクスポート
2. Webインターフェースでファイルをアップロード
3. AI処理が自動的に実行され、SOAP形式の診療記録が生成
4. 必要に応じて編集し、データベースに保存

### 3. Python APIとしての使用

```python
from dental_ai_database import DentalAIDatabase

# データベースの初期化
db = DentalAIDatabase('dental_counseling.db')

# ファイル処理
result = db.process_file('path/to/recording.txt', 'plaud')

# SOAP記録の表示
print(f"S: {result['soap']['subjective']}")
print(f"O: {result['soap']['objective']}")
print(f"A: {result['soap']['assessment']}")
print(f"P: {result['soap']['plan']}")
```

## プロジェクト構造

```
dental-counseling-ai/
├── ui/                     # WebUIファイル
│   ├── index.html         # メインHTML
│   ├── styles.css         # スタイルシート
│   ├── script.js          # メインJavaScript
│   └── gemini_integration.js  # AI統合
├── dental_counseling_ai/   # Pythonパッケージ
│   ├── core/              # コア機能
│   ├── database/          # データベース関連
│   └── api/               # API実装
├── dental_ai_database.py   # メインデータベースクラス
├── database_schema.sql     # データベーススキーマ
└── README.md              # このファイル
```

## API仕様

### ファイル処理エンドポイント

```javascript
// ファイルアップロード
POST /api/process
Content-Type: multipart/form-data

// レスポンス
{
  "session_id": "xxx",
  "patient_name": "患者名",
  "doctor_name": "医師名",
  "soap": {
    "subjective": "主観的情報",
    "objective": "客観的所見",
    "assessment": "評価",
    "plan": "計画"
  },
  "quality": {
    "communication_quality": 0.85,
    "patient_understanding": 0.90,
    "consent_likelihood": 0.88
  }
}
```

## 設定

### Google Gemini API (オプション)

より高度なAI処理を利用する場合：

```javascript
// ui/gemini_integration.js
const API_KEY = 'your-gemini-api-key';
```

## 開発

### 開発環境のセットアップ

```bash
# 開発用依存関係のインストール
pip install -r requirements-dev.txt

# テストの実行
python -m pytest

# コードフォーマット
black .
```

### ブランチ戦略

- `main`: 本番環境用
- `develop`: 開発用
- `feature/*`: 新機能開発
- `fix/*`: バグ修正

## トラブルシューティング

### よくある問題

1. **文字が見えない**
   - ブラウザのズームレベルを100%に設定
   - CSSのコントラスト設定を確認

2. **ファイルが処理されない**
   - 対応ファイル形式を確認
   - ファイルサイズが大きすぎないか確認（推奨: 10MB以下）

3. **AI処理がタイムアウトする**
   - インターネット接続を確認
   - Gemini APIキーの有効性を確認

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを作成して変更内容について議論してください。

## 作者

- Your Name (@yourusername)

## 謝辞

- PLAUD NOTEおよびNottaチーム
- Google Gemini API
- すべてのコントリビューター