# 歯科カウンセリング音声記録AIツール

歯科カウンセリングの音声を自動で記録・分析し、SOAP形式のカルテに変換するプロトタイプシステムです。

## 🎯 主な機能

- **音声データ処理**: PLAUD NOTEやNottaなど異なる形式のデータを統一処理
- **患者・医師自動特定**: 録音データと予約システムを照合して自動特定
- **SOAP形式変換**: 文字起こしテキストから歯科用SOAP形式カルテを自動生成
- **Webインターフェース**: 録音制御、SOAP確認・編集、レセコン連携機能
- **データ分析基盤**: 音声の非言語情報と成約率の相関分析（将来拡張）

## 🏗️ システム構成

```
dental_counseling_ai/
├── core/                    # コア機能
│   ├── data_processor.py    # データ処理エンジン
│   ├── patient_matcher.py   # 患者・医師特定ロジック
│   └── soap_generator.py    # SOAP形式変換エンジン
├── database/                # データベース
│   └── models.py           # SQLAlchemyモデル定義
├── api/                     # API・Webインターフェース
│   └── main.py             # FastAPI メインアプリケーション
├── test_integration.py      # 統合テスト
├── requirements.txt         # 依存関係
└── README.md               # このファイル
```

## 🚀 セットアップ・実行方法

### 1. 依存関係のインストール

```bash
cd dental_counseling_ai
pip install -r requirements.txt
```

### 2. 統合テストの実行

```bash
python test_integration.py
```

このテストでは以下の処理が実行されます：
- サンプルデータファイルの作成
- データ処理機能のテスト
- 患者マッチング機能のテスト
- SOAP生成機能のテスト
- データベース操作のテスト

### 3. Webアプリケーションの起動

```bash
python api/main.py
```

ブラウザで `http://localhost:8000` にアクセスしてWebインターフェースを使用できます。

## 📋 使用方法

### Webインターフェース

1. **録音制御**
   - 医師IDを入力
   - 「録音開始」ボタンでセッション開始
   - 「録音停止」ボタンで処理実行・SOAP生成

2. **ファイルアップロード**
   - PLAUD NOTEやNottaの出力ファイルをアップロード
   - 自動でデータ処理・SOAP生成

3. **SOAP確認・編集**
   - 生成されたSOAPの確認・修正
   - レセコンへの送信（ダミー実装）

### API エンドポイント

- `POST /api/sessions/start` - 録音セッション開始
- `POST /api/sessions/stop/{session_id}` - 録音停止・処理実行
- `POST /api/upload` - ファイルアップロード・処理
- `GET /api/sessions/{session_id}` - セッション詳細取得
- `PUT /api/sessions/soap` - SOAP更新
- `POST /api/sessions/{session_id}/submit-to-rececon` - レセコン送信

## 📊 対応データ形式

### PLAUD NOTE
- **文字起こし**: TXT, SRT, DOCX, PDF
- **要約**: TXT, Markdown, DOCX, PDF
- **音声**: MP3, WAV

### Notta
- **文字起こし**: TXT, DOCX, SRT, PDF, CSV, XLSX
- **音声**: MP3, WAV

## 🗄️ データベース構造

### counseling_sessions
- セッション基本情報（患者ID、医師ID、音声ファイル、SOAP等）

### voice_analytics
- 音声分析データ（声色、感情指標、非言語イベント等）

### counseling_outcomes
- カウンセリング結果（成約/非成約、金額、フォローアップ等）

## 🔧 カスタマイズ・拡張

### 歯科専門用語の追加
`core/soap_generator.py` の `dental_terms` 辞書を編集

### 新しいデータ形式の対応
`core/data_processor.py` に新しい処理メソッドを追加

### 音声感情分析の統合
`core/` に新しいモジュールを追加し、AmiVoice ESAS等のAPIを統合

## ⚠️ 注意事項

- これはプロトタイプ実装です
- 実際の音声認識機能は未実装（ダミーデータを使用）
- レセコン連携は概念実装のみ
- 本格運用には追加のセキュリティ対策が必要

## 🔮 将来の拡張予定

- 実際の音声認識エンジン統合（Whisper、AmiVoice等）
- 音声感情分析機能（AmiVoice ESAS等）
- レセコンとの実際のAPI連携
- 成約率分析・予測機能
- HL7 FHIR準拠のデータ出力

## 📞 サポート

技術的な質問や改善提案がありましたら、開発チームまでお問い合わせください。