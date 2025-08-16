# Claude Code 起動ガイド

## 🚨 重要：統一起動方法

### 推奨手順：
1. `cd /Users/dd/Desktop/1_dev/coding-rule2`
2. Claude Code を起動
3. `cd projects/YOUR_PROJECT` で作業開始

### なぜこの方法？
- ✅ o3, gemini, brave-search が使用可能
- ✅ 全21個のMCPサーバーアクセス
- ✅ 環境変数完全読み込み
- ✅ プロジェクト文脈自動検出

### ❌ 避けるべき：
- このディレクトリから直接Claude Code起動
- MCP不具合の原因となります

**起動ガイド実行**: `python3 /Users/dd/Desktop/1_dev/coding-rule2/scripts/tools/claude_code_startup_guide.py`
