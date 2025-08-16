# 歯科カウンセリングAIツール（UI）

## 概要
PLAUD NOTE / Notta などの書き起こしファイルを解析し、歯科に特化した SOAP 形式（S/O/A/P）の診療記録を自動生成します。オフラインでも動作し、API接続時はより高精度な処理に切り替わります。

## 主な機能
- ファイル解析（PLAUD/NottaのTXT, CSV, SRT, MD）
- 患者/医師の自動識別（AI+ルール統合、オフライン可）
- SOAP生成（AI接続時は高精度、未接続時はフォールバック）
- 品質分析スコア（会話量/理解確認/同意傾向）
- JSONL 形式での保存（ローカルストレージ＋サーバ保存）

## 対応形式と現状の制限
- 対応: `.txt`, `.csv`, `.srt`, `.md`
- 未対応（ガイド表示）: `.xlsx`（Notta は CSV エクスポートして利用）
- 音声: `.mp3`, `.wav` は文字起こし未実装（SRT/TXT を利用）

## 起動方法（用途別）
1) 簡易UIのみ（オフライン可）
```bash
cd ui
python -m http.server 8000
# http://localhost:8000
```

2) 統合サーバ（UI+API 同一オリジン）
```bash
python ui/demo.py   # 既定: port 8001（ポート管理システムに従う）
```

3) 代替APIサーバのみ（必要時）
```bash
python ui/api_server.py 8002
```

## サーバ保存（任意機能）
- エンドポイント: `POST /api/save_jsonl`
- 内容: JSON（1件）を 1 行 JSONL として `ui/sessions.jsonl` に追記
- UI 側はローカル保存に加えて存在時に自動送信（失敗は無視）

## 設定
- APIエンドポイントは `window.DENTAL_API_ENDPOINT` が存在すればそれを優先。未指定時は既定値を使用します。

## ファイル構成
- `index.html` / `styles.css` / `script.js`（UI本体）
- `gemini_integration.js`（API連携とフォールバック処理）
- `demo.py`（UI+API 統合サーバ）
- `api_server.py`（代替APIサーバ）

## 備考
- 端末のローカルストレージに JSONL を保存します。長期保存や集約にはサーバ保存機能の利用を推奨します。
