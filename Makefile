# Dental Project Makefile
# 1_dev Global Commands Proxy

PARENT_MAKEFILE := ../Makefile

.PHONY: help claude-launch claude-test claude-status dev

# Default help - プロジェクト固有 + グローバルコマンド
help:
	@echo "🦷 Dental System Project Commands"
	@echo "================================="
	@echo ""
	@echo "🚀 Claude Code (Global System):"
	@echo "  claude-launch    - 🚀 統一Claude Code起動 (全MCP利用可能)"
	@echo "  claude-test      - 🔍 MCP機能テスト実行" 
	@echo "  claude-status    - 📊 Claude Code システム状況"
	@echo ""
	@echo "🎯 Project Commands:"
	@echo "  dev              - 🏃 開発モード起動"
	@echo "  install          - 📦 依存関係インストール"
	@echo ""
	@echo "💡 推奨ワークフロー:"
	@echo "  1. make claude-launch  (Claude Code起動)"
	@echo "  2. make dev           (プロジェクト開発開始)"

# Claude Code統一コマンド (親Makefileにプロキシ)
claude-launch:
	@make -f $(PARENT_MAKEFILE) claude-launch

claude-test:
	@make -f $(PARENT_MAKEFILE) claude-test

claude-status:
	@make -f $(PARENT_MAKEFILE) claude-status

# プロジェクト固有コマンド
dev:
	@echo "🦷 Dental System Development Mode"
	@echo "================================="
	@if [ -d "ui" ]; then \
		echo "🌐 UI directory found. Starting web interface..."; \
		if [ -f "ui/package.json" ]; then \
			cd ui && npm run dev || npm start || echo "⚠️  No dev/start script in ui/package.json"; \
		elif [ -f "ui/index.html" ]; then \
			echo "📄 Static HTML found. Use a local server:"; \
			echo "   cd ui && python3 -m http.server 8000"; \
		fi \
	elif [ -f "main.py" ]; then \
		echo "🐍 Starting with Python..."; \
		python3 main.py; \
	elif [ -f "app.py" ]; then \
		echo "🐍 Starting with Python (app.py)..."; \
		python3 app.py; \
	else \
		echo "⚠️  No standard entry point found"; \
		echo "📋 Available files:"; \
		ls -la | head -10; \
	fi

install:
	@echo "📦 Installing Dental System Dependencies"
	@echo "======================================="
	@if [ -d "ui" ] && [ -f "ui/package.json" ]; then \
		echo "Installing UI dependencies..."; \
		cd ui && npm install; \
	fi
	@if [ -f "requirements.txt" ]; then \
		echo "Installing Python dependencies..."; \
		pip3 install -r requirements.txt; \
	fi
	@if [ -d "venv" ]; then \
		echo "Virtual environment found. Activating..."; \
		echo "Note: Run 'source venv/bin/activate' manually"; \
	fi
	@echo "✅ Dependencies installation completed"