# 🔧 Vercel環境変数設定ガイド

## 🎯 設定すべき環境変数

### 必須API変数
```bash
# OpenRouter (GPT-5-chat用)
OPENROUTER_API_KEY=[OpenRouter APIキーをここに入力]
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# OpenAI (GPT-4用)
OPENAI_API_KEY=[OpenAI APIキーをここに入力]

# Gemini (Google AI用)
GEMINI_API_KEY=[Gemini APIキー]

# データベース
SUPABASE_URL=https://hetcpqtsineqaopnnvtn.supabase.co
SUPABASE_ANON_KEY=[Supabaseキー]
```

## 📋 Vercel Dashboard設定手順

### ステップ1: プロジェクト設定
1. https://vercel.com/dashboard にアクセス
2. dental プロジェクトを選択
3. **Settings** タブをクリック

### ステップ2: 環境変数追加
1. **Environment Variables** セクションを選択
2. **Add** ボタンをクリック
3. 各変数を以下の形式で追加:

```
Name: OPENROUTER_API_KEY
Value: [実際のOpenRouterAPIキーをここに入力]
Environment: Production, Preview, Development

Name: OPENROUTER_BASE_URL  
Value: https://openrouter.ai/api/v1
Environment: Production, Preview, Development

Name: OPENAI_API_KEY
Value: [実際のOpenAIAPIキーをここに入力]
Environment: Production, Preview, Development
```

### ステップ3: 再デプロイ
1. **Deployments** タブに移動
2. 最新デプロイメントの **...** メニュー
3. **Redeploy** を選択

## 🚨 重要注意事項

### APIキー取得
- **OpenRouter**: https://openrouter.ai/settings で確認
- **OpenAI**: https://platform.openai.com/api-keys で確認
- **Gemini**: https://makersuite.google.com/app/apikey で取得

### セキュリティ
- 本番環境では新しいAPIキーを生成推奨
- キーの定期ローテーション実施
- 使用量監視設定

## ✅ 動作確認方法

### デプロイ後テスト
1. プロダクション環境でファイルアップロード
2. OpenRouter → OpenAI → Gemini フォールバック確認
3. エラーログでAPI接続状況確認

### エラー解決
- **500エラー**: 環境変数名・値の確認
- **403エラー**: APIキー有効性確認
- **タイムアウト**: APIサービス状況確認