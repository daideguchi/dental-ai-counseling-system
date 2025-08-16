# Agents Hub: Dental Counseling AI

このドキュメントは Codex と Claude Code の共同作業ハブです。現在の実装状況、決定事項、実行方法、次のタスク、連携プロトコルを一か所に集約します。

## 現状サマリ
- 目的: 音声記録（PLAUD/Notta）から歯科特化のSOAP記録を自動生成し、品質分析と履歴管理を提供。
- 主要UI: `ui/index.html` + `ui/script.js` + `ui/styles.css`
- AI連携: `ui/gemini_integration.js`（API接続あり/なしで自動フォールバック）
- 代替API: `ui/demo.py`（UI+API統合）, `ui/api_server.py`（API単体）
- 永続化: ブラウザlocalStorageにJSONL保存＋任意で`/api/save_jsonl`に送信（`ui/sessions.jsonl`追記）＋`/api/save_sqlite`でSQLite保存（`ui/dental_counseling.db`）

## 直近の変更（Codex + Claude Code実施）
1) APIエンドポイント外部上書き（互換維持）
- `ui/gemini_integration.js` に `window.DENTAL_API_ENDPOINT` を導入（未設定時は従来`http://localhost:8000/api/gemini`）。

2) SQLite永続化実装（Claude Code - 完了）
- 追記保存: `POST /api/save_jsonl`（1 JSON → `ui/sessions.jsonl` に1行追記）
- SQLite保存: `POST /api/save_sqlite`（1 JSON → `ui/dental_counseling.db` に保存）
- 実装: `ui/demo.py`, `ui/api_server.py`, `ui/db.py`
- UI: `saveToDatabase()` 実行時にローカル保存＋サーバ送信（両エンドポイントを順次試行、失敗は警告ログ）

3) XLSX解析機能実装（Claude Code - 完了）
- サーバーサイド: `ui/xlsx_parser.py` - 外部依存なしのXLSX解析モジュール
- API追加: `POST /api/parse_xlsx` - multipart/form-dataでXLSXファイルを受信・解析
- UI統合: `ui/script.js` で XLSX ファイル自動検出・専用API呼び出し
- UXガイド更新: XLSX選択時に「サーバー側で自動解析」をアナウンス（`.mp3/.wav`: 文字起こし未実装のため SRT/TXT を案内）

4) JavaScript安定性改善（Claude Code - 完了）
- DOM操作nullチェック追加: innerHTML代入前のnullチェックを全箇所に実装
- エラーハンドリング強化: 「Cannot set properties of null」エラーの根絶
- ファイルリスト表示の安全化: DOM要素不在時の適切なエラー処理

5) ドキュメント修復
- `ui/README.md` を再作成（対応形式・起動方法・保存API・設定を明確化）

## 実行方法（ポートは既存システム準拠）
- UIのみ（オフライン動作可）: `cd ui && python -m http.server 8000` → `http://localhost:8000`
- 統合サーバ（UI+API）: `python ui/demo.py`（デフォルト 8001）
- API単体: `python ui/api_server.py 8002`

API接続をUIに認識させるには、ページロード前に以下を設定可能:
```html
<script>
  window.DENTAL_API_ENDPOINT = 'http://localhost:8001/api/gemini';
</script>
```

## エンドポイント一覧
- 健康診断: `GET /api/gemini/health`
- 識別: `POST /api/gemini/identify`
- SOAP: `POST /api/gemini/soap`
- 品質: `POST /api/gemini/quality`（demo.py のみ）
- 保存: `POST /api/save_jsonl`（JSONL追記）, `POST /api/save_sqlite`（SQLite保存）
- XLSX解析: `POST /api/parse_xlsx`（XLSXファイル → テキスト変換）

## 次に実装したい項目（提案）
- 音声STT統合: Whisper等を使った `/api/transcribe` を追加し、mp3/wav→テキスト→既存フローに接続
- DB正規化: `custom_database_schema.sql` に沿った詳細スキーマへの拡張
- XLSX解析精度向上: 会話識別ロジックの改善（発話者・時刻パターン認識）
- UI/UX改善: エラーメッセージ・プログレス表示の充実

優先度（推奨）
1. ✅ SQLite永続化（実装済み・動作確認済み）
2. ✅ XLSXサポート（実装済み・外部依存なし）  
3. 音声STT統合（次の機能拡張として高価値）
4. DB正規化・UI改善（品質向上）

## 検証チェックリスト
- ✅ UIのみで TXT/CSV/SRT/MD が処理でき、SOAP/品質スコアが表示される
- ✅ API接続時、より詳細な結果が返る（エラー時はフォールバック動作）
- ✅ 保存操作で localStorage、`ui/sessions.jsonl`（存在時）、`ui/dental_counseling.db`（存在時）が更新される
- ✅ `.xlsx` ファイルがサーバー側で自動解析・テキスト変換される
- ✅ `.mp3/.wav` 選択時にガイドが出て、処理ボタンが抑止される
- ✅ JavaScript DOM エラーが解決され、処理ログが正常表示される

## 連携プロトコル（更新の流れ）
1. 作業者は本ハブに「変更サマリ、意図、影響、検証方法」を追記
2. 変更が複数ファイルに跨る場合、ここに関連箇所を列挙
3. 保留/次タスクは本ハブの一覧に追加し、担当（Codex/Claude）を明示

## 参考ファイル
- `ui/script.js`（中核）
- `ui/gemini_integration.js`（API連携とフォールバック）
- `ui/demo.py`（UI+API統合サーバ）
- `ui/api_server.py`（API単体）
- `ui/README.md`（UIの使い方）

---

### Claude Code 向けハンドオフ要約（短文）
プロダクトはUI主体で、API接続の有無に応じてフォールバック動作します。ポート変更は不要で、`window.DENTAL_API_ENDPOINT` でAPIルートを上書き可能。主要機能が完成：✅SQLite永続化（`ui/db.py`）✅XLSX解析（`ui/xlsx_parser.py`、外部依存なし）✅JavaScript安定性改善（DOMnullチェック）。UI保存時に `/api/save_jsonl`、`/api/save_sqlite` が実行されます。次は「音声STT統合」か「DB正規化」を検討。詳細は本ハブ参照。
