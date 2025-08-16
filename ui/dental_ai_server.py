#!/usr/bin/env python3
"""
歯科AIツール統合サーバー（Gemini AI処理エンジン搭載）
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import json
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict
import google.generativeai as genai
import time

# 統一ポート管理システム統合
sys.path.append('/Users/dd/Desktop/1_dev/shared/scripts')
try:
    from unified_port_manager import UnifiedPortManager, setup_unified_signal_handlers, quick_allocate_port
    unified_port_manager_available = True
except Exception:
    unified_port_manager_available = False
    print("⚠️ 統一ポート管理システムが利用できません")

try:
    # Optional: SQLite persistence
    import db as dbmod  # type: ignore
except Exception:
    dbmod = None

try:
    # Optional: XLSX parsing
    import xlsx_parser as xlsxmod  # type: ignore
except Exception:
    xlsxmod = None

class DentalUIHandler(http.server.SimpleHTTPRequestHandler):
    
    def __init__(self, *args, **kwargs):
        # Gemini API初期化
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            print(f"🔍 DEBUG: API Key found: {bool(api_key)}")
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                self.ai_available = True
                print("✅ Gemini API初期化完了")
            else:
                self.ai_available = False
                print("❌ GEMINI_API_KEYが設定されていません")
        except Exception as e:
            print(f"❌ Gemini API初期化エラー: {e}")
            self.ai_available = False
        super().__init__(*args, **kwargs)
    
    def end_headers(self):
        # CORS対応
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Version')
        super().end_headers()

    def do_OPTIONS(self):
        """CORS対応のためのOPTIONSハンドラ"""
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        """GETリクエストハンドラ（API対応）"""
        if self.path == '/api/gemini/health':
            self.send_health_check()
        else:
            # 通常のファイル配信
            super().do_GET()

    def do_POST(self):
        """POSTリクエストハンドラ（API対応）"""
        if self.path == '/api/gemini/identify':
            self.handle_identify_request()
        elif self.path == '/api/gemini/soap':
            self.handle_soap_request()
        elif self.path == '/api/gemini/quality':
            self.handle_quality_request()
        elif self.path == '/api/save_jsonl':
            self.handle_save_jsonl()
        elif self.path == '/api/save_sqlite':
            self.handle_save_sqlite()
        elif self.path == '/api/parse_xlsx':
            self.handle_xlsx_parsing()
        else:
            self.send_error(404, "API Not Found")

    def send_health_check(self):
        """ヘルスチェック応答"""
        response = {
            "status": "healthy",
            "service": "dental_ai_integrated",
            "version": "1.0.0",
            "timestamp": "2025-08-06T21:55:00Z",
            "endpoints": ["/api/gemini/health", "/api/gemini/identify", "/api/gemini/soap", "/api/gemini/quality", "/api/parse_xlsx"],
            "integration": "ui_server_embedded"
        }
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False, indent=2).encode('utf-8'))
        print("✅ API Health Check 応答送信")

    def handle_identify_request(self):
        """患者・医師識別リクエスト処理"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            conversation = request_data.get('content', request_data.get('conversation', ''))
            print(f"🔍 患者・医師識別要求: {len(conversation)}文字")
            
            # 高精度患者・医師識別（完全版）
            result = self.identify_patient_doctor_advanced(conversation)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False, indent=2).encode('utf-8'))
            print(f"✅ 患者・医師識別完了: {result['patient_name']}, {result['doctor_name']}")
            
        except Exception as e:
            print(f"❌ 識別処理エラー: {e}")
            error_response = {
                "patient_name": "患者",
                "doctor_name": "医師", 
                "confidence_patient": 0.3,
                "confidence_doctor": 0.3,
                "error": str(e),
                "method": "fallback_error"
            }
            self.send_response(200)  # エラーでも200を返してフロントエンドが動作するように
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

    def handle_soap_request(self):
        """SOAP変換リクエスト処理"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            conversation = request_data.get('content', request_data.get('conversation', ''))
            patient_name = request_data.get('patient_name', '患者')
            doctor_name = request_data.get('doctor_name', '医師')
            print(f"📋 SOAP変換要求: 患者={patient_name}, 医師={doctor_name}")
            
            # 高精度SOAP変換（完全版）
            result = self.convert_to_soap_advanced(conversation, patient_name, doctor_name)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False, indent=2).encode('utf-8'))
            print("✅ SOAP変換完了")
            
        except Exception as e:
            print(f"❌ SOAP変換エラー: {e}")
            error_response = {
                "S": "主観的情報（患者の訴え）",
                "O": "客観的所見（医師の観察）",
                "A": "評価・診断",
                "P": "治療計画",
                "confidence": 0.3,
                "error": str(e),
                "method": "fallback_error"
            }
            self.send_response(200)  # エラーでも200を返す
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

    def handle_quality_request(self):
        """品質分析リクエスト処理"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            conversation = request_data.get('content', request_data.get('conversation', ''))
            soap_data = request_data.get('soap', {})
            print(f"📊 品質分析要求: {len(conversation)}文字")
            
            # 高精度品質分析（完全版）
            result = self.analyze_quality_advanced(conversation, soap_data)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False, indent=2).encode('utf-8'))
            print("✅ 品質分析完了")
            
        except Exception as e:
            print(f"❌ 品質分析エラー: {e}")
            error_response = {
                "communication_quality": 0.7,
                "patient_understanding": 0.6,
                "treatment_consent_likelihood": 0.5,
                "improvement_suggestions": ["詳細な分析にはより高度なAIが必要です"],
                "positive_aspects": ["会話が記録されています"],
                "confidence": 0.3,
                "error": str(e),
                "method": "fallback_quality_error"
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

    def analyze_quality_advanced(self, conversation, soap_data):
        """実際のGemini AIを使用した品質分析"""
        
        # AI が利用できない場合のみフォールバック
        if not self.ai_available or not hasattr(self, 'gemini_model'):
            print("⚠️ WARNING: Gemini API利用不可 - 品質分析フォールバック実行")
            return self._fallback_quality_analysis(conversation)
        
        # AI分析を強制実行 - 複数回試行
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🤖 Gemini AI品質分析実行中... (試行 {attempt + 1}/{max_retries})")
                
                prompt = f"""
あなたは歯科医療専門のAI分析ツールです。以下の歯科医師と患者の会話を分析し、コミュニケーション品質を評価してください。

【会話内容】
{conversation}

【SOAP記録】
主観的情報(S): {soap_data.get('subjective', 'N/A')}
客観的所見(O): {soap_data.get('objective', 'N/A')}
評価・診断(A): {soap_data.get('assessment', 'N/A')}
治療計画(P): {soap_data.get('plan', 'N/A')}

以下の項目を0.0から1.0のスコアで評価し、JSON形式で回答してください：

1. communication_quality: コミュニケーション全体の質（説明の明確性、共感性など）
2. patient_understanding: 患者の理解度（質問への回答、確認の有無など）  
3. treatment_consent_likelihood: 治療への同意可能性（患者の前向きさ、不安の解消など）
4. improvement_suggestions: 改善提案（配列、具体的なアドバイス）
5. positive_aspects: 良い点（配列、評価できる要素）
6. confidence: 分析の信頼度（0.0-1.0）

必ずJSON形式で回答してください。説明文は不要です。
"""

                response = self.gemini_model.generate_content(prompt)
                print(f"🔍 DEBUG: Quality Gemini API Raw Response: '{response.text}'")
                
                # JSONのパース
                # JSONコードブロックを除去してパース
                clean_response = response.text.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]  # ```json を除去
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]  # ``` を除去
                clean_response = clean_response.strip()
                
                print(f"🔍 DEBUG: Quality Cleaned Response: '{clean_response}'")
                result = json.loads(clean_response)
                
                # 処理ログ追加
                result["process_log"] = [
                    "🤖 Gemini AI品質分析開始",
                    f"📝 解析対象: {len(conversation.split())}文字の医療会話",
                    "🧠 自然言語処理による深層分析実行",
                    f"📊 コミュニケーション品質: {result.get('communication_quality', 0):.2f}",
                    f"📊 患者理解度: {result.get('patient_understanding', 0):.2f}",
                    f"📊 治療同意可能性: {result.get('treatment_consent_likelihood', 0):.2f}",
                    f"✅ Gemini AI分析完了（信頼度: {result.get('confidence', 0):.2f}）"
                ]
                result["method"] = "gemini_ai_natural_language_processing"
                
                print(f"✅ Gemini AI品質分析完了: {result['confidence']:.2f}信頼度")
                return result
                
            except json.JSONDecodeError as e:
                print(f"❌ Gemini AIのJSON応答パースエラー (試行 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    break  # 最後の試行なのでループを抜ける
                continue  # 次の試行
                
            except Exception as e:
                print(f"❌ Gemini AI品質分析エラー (試行 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    break  # 最後の試行なのでループを抜ける
                continue  # 次の試行
        
        # 全ての試行が失敗した場合のみフォールバック
        print(f"⚠️ {max_retries}回の試行すべてが失敗 - 品質分析フォールバック実行")
        return self._fallback_quality_analysis(conversation)
    
    def _execute_ai_with_retry(self, prompt, max_retries=3):
        """リトライ機能付きAI実行（指数バックオフ）"""
        for attempt in range(max_retries):
            try:
                response = self.gemini_model.generate_content(prompt)
                result = json.loads(response.text)
                
                print(f"✅ AI処理成功（試行 {attempt + 1}/{max_retries}）")
                return result
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析エラー（試行 {attempt + 1}/{max_retries}）: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # 指数バックオフ
                
            except Exception as e:
                print(f"❌ AI処理エラー（試行 {attempt + 1}/{max_retries}）: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # 指数バックオフ
        
        return None
    
    def _fallback_quality_analysis(self, conversation):
        """AI処理失敗時のフォールバック - 実際の会話内容から分析"""
        lines = conversation.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        
        # 会話の基本指標を計算
        patient_lines = len([line for line in lines if '患者:' in line])
        doctor_lines = len([line for line in lines if '医師:' in line])
        
        # コミュニケーション品質 (会話のバランス)
        if patient_lines > 0 and doctor_lines > 0:
            balance_ratio = min(patient_lines, doctor_lines) / max(patient_lines, doctor_lines)
            communication_quality = 0.3 + (balance_ratio * 0.4)  # 0.3-0.7の範囲
        else:
            communication_quality = 0.2
        
        # 患者理解度 (質問への回答の有無)
        question_indicators = ['？', '?', 'どの', 'いつ', 'どこ', 'なぜ', 'どうして']
        questions = sum(1 for line in lines for indicator in question_indicators if indicator in line)
        patient_understanding = min(0.9, 0.4 + (questions * 0.1))
        
        # 治療同意可能性 (ポジティブな反応)
        positive_indicators = ['はい', 'お願いします', '分かりました', 'そうします']
        positive_responses = sum(1 for line in lines for indicator in positive_indicators if indicator in line)
        treatment_consent = min(0.9, 0.3 + (positive_responses * 0.15))
        
        # 改善提案
        suggestions = []
        if communication_quality < 0.5:
            suggestions.append("医師と患者の発言バランスの改善が推奨されます")
        if patient_understanding < 0.6:
            suggestions.append("患者への説明をより丁寧に行うことを推奨します")
        if treatment_consent < 0.5:
            suggestions.append("患者の同意を確認する機会を増やすことを推奨します")
        
        if not suggestions:
            suggestions.append("会話の流れは良好です")
        
        # 良い点
        positive_aspects = []
        if total_lines >= 10:
            positive_aspects.append("十分な会話時間が確保されています")
        if patient_lines >= 3:
            positive_aspects.append("患者の発言機会が適切に設けられています")
        if doctor_lines >= 3:
            positive_aspects.append("医師による十分な説明が行われています")
        
        if not positive_aspects:
            positive_aspects.append("会話が記録されています")
        
        return {
            "communication_quality": round(communication_quality, 2),
            "patient_understanding": round(patient_understanding, 2), 
            "treatment_consent_likelihood": round(treatment_consent, 2),
            "improvement_suggestions": suggestions,
            "positive_aspects": positive_aspects,
            "confidence": 0.6,  # テキスト分析なので中程度の信頼度
            "method": "text_analysis_fallback",
            "process_log": [
                "❌ AI分析失敗",
                "📝 テキスト解析フォールバックモード",
                "⚠️ Gemini API利用不可",
                f"✅ 会話解析完了: 総行数{total_lines}, 患者発言{patient_lines}, 医師発言{doctor_lines}"
            ]
        }

    def handle_save_jsonl(self):
        """JSONLレコードをサーバ側に追記保存"""
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length)
            data = json.loads(raw.decode('utf-8'))
            # 1行のJSONとして保存
            target = Path(__file__).parent / 'sessions.jsonl'
            with target.open('a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}, ensure_ascii=False).encode('utf-8'))
            print(f"💾 サーバ保存: {target.name} に追記")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False).encode('utf-8'))
            print(f"❌ サーバ保存エラー: {e}")

    def handle_save_sqlite(self):
        """JSONレコードをSQLiteに保存（ui/db.py使用）"""
        try:
            if dbmod is None:
                raise RuntimeError("SQLite module not available")
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length)
            data: Dict[str, Any] = json.loads(raw.decode('utf-8'))
            conn = dbmod.connect()
            dbmod.init_db(conn)
            session_id = dbmod.save_jsonl_record(conn, data)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "session_id": session_id}, ensure_ascii=False).encode('utf-8'))
            print(f"💾 SQLite保存: session_id={session_id}")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False).encode('utf-8'))
            print(f"❌ SQLite保存エラー: {e}")

    def handle_xlsx_parsing(self):
        """XLSXファイル解析API（外部依存なし）"""
        try:
            if xlsxmod is None:
                raise RuntimeError("XLSX parser module not available")
            
            # multipart/form-data を解析
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                raise ValueError("Content-Type must be multipart/form-data")
            
            length = int(self.headers.get('Content-Length', 0))
            raw_data = self.rfile.read(length)
            
            # 簡易的なmultipartパース（ファイルデータ部分を抽出）
            boundary = content_type.split('boundary=')[1].encode()
            parts = raw_data.split(b'--' + boundary)
            
            xlsx_content = None
            for part in parts:
                if b'filename=' in part and (b'.xlsx' in part.lower() or b'.xls' in part.lower()):
                    # ヘッダーとデータを分離
                    if b'\r\n\r\n' in part:
                        _, file_data = part.split(b'\r\n\r\n', 1)
                        xlsx_content = file_data.rstrip(b'\r\n')
                        break
            
            if xlsx_content is None:
                raise ValueError("XLSX file not found in request")
            
            # XLSX解析実行
            parse_result = xlsxmod.parse_xlsx_file(xlsx_content)
            
            if parse_result.get("success", False):
                # 会話形式に変換
                formatted_text = xlsxmod.format_as_conversation(parse_result)
                
                response = {
                    "success": True,
                    "text_content": formatted_text,
                    "original_result": parse_result,
                    "message": f"XLSX解析完了: {parse_result.get('line_count', 0)}行のテキストを抽出"
                }
            else:
                response = {
                    "success": False,
                    "error": parse_result.get("error", "解析失敗"),
                    "text_content": "",
                    "message": "XLSXファイルの解析に失敗しました"
                }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
            print(f"📊 XLSX解析: {response.get('message', 'unknown')}")
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            error_response = {
                "success": False,
                "error": str(e),
                "text_content": "",
                "message": f"XLSX解析エラー: {e}"
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
            print(f"❌ XLSX解析エラー: {e}")

    def identify_patient_doctor_advanced(self, conversation):
        """実際のGemini AIを使用した患者・医師識別"""
        print(f"🔍 DEBUG: ai_available = {self.ai_available}")
        print(f"🔍 DEBUG: hasattr gemini_model = {hasattr(self, 'gemini_model')}")
        
        # AI が利用できない場合のみフォールバック
        if not self.ai_available or not hasattr(self, 'gemini_model'):
            print("⚠️ WARNING: Gemini API利用不可 - フォールバック実行")
            return self._fallback_identify(conversation)
        
        # AI分析を強制実行 - 複数回試行
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🤖 Gemini AI識別実行中... (試行 {attempt + 1}/{max_retries})")
                
                prompt = f"""
あなたは歯科医療専門のAI分析ツールです。以下の歯科医師と患者の会話から、正確な名前を抽出してください。

【会話内容】
{conversation}

以下のJSON形式で回答してください：
{{
    "patient_name": "抽出された患者名（見つからない場合は'患者'）",
    "doctor_name": "抽出された医師名（見つからない場合は'医師'）",
    "confidence_patient": 信頼度（0.0-1.0）,
    "confidence_doctor": 信頼度（0.0-1.0）,
    "reasoning": "判断根拠の説明"
}}

重要な注意事項：
- 医療用語（診察、治療、拝見など）を名前と誤認しないでください
- 敬語表現（いらっしゃいませ、ございますなど）を名前と誤認しないでください  
- 応答語（はい、そうですなど）を名前と誤認しないでください
- 実際の人名のみを抽出してください
- Dr.田中、田中先生のような明確な名前指定を優先してください

必ずJSON形式で回答してください。説明文は不要です。
"""

                response = self.gemini_model.generate_content(prompt)
                print(f"🔍 DEBUG: Gemini API Raw Response: '{response.text}'")
                
                # JSONコードブロックを除去してパース
                clean_response = response.text.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]  # ```json を除去
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]  # ``` を除去
                clean_response = clean_response.strip()
                
                print(f"🔍 DEBUG: Cleaned Response: '{clean_response}'")
                result = json.loads(clean_response)
                
                # 処理ログ追加
                result["process_log"] = [
                    "🤖 Gemini AI患者・医師識別開始",
                    f"📝 解析対象: {len(conversation)}文字の医療会話データ",
                    "🧠 自然言語処理による名前抽出実行",
                    f"👤 患者識別: '{result.get('patient_name', '患者')}' (信頼度: {result.get('confidence_patient', 0):.2f})",
                    f"👨‍⚕️ 医師識別: '{result.get('doctor_name', '医師')}' (信頼度: {result.get('confidence_doctor', 0):.2f})",
                    f"✅ Gemini AI識別完了"
                ]
                result["method"] = "gemini_ai_named_entity_recognition"
                
                print(f"✅ Gemini AI患者・医師識別完了: {result['patient_name']}, {result['doctor_name']}")
                return result
                
            except json.JSONDecodeError as e:
                print(f"❌ Gemini AIのJSON応答パースエラー (試行 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    break  # 最後の試行なのでループを抜ける
                continue  # 次の試行
                
            except Exception as e:
                print(f"❌ Gemini AI識別エラー (試行 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    break  # 最後の試行なのでループを抜ける
                continue  # 次の試行
        
        # 全ての試行が失敗した場合のみフォールバック
        print(f"⚠️ {max_retries}回の試行すべてが失敗 - フォールバック実行")
        return self._fallback_identify(conversation)
    
    def _fallback_identify(self, conversation):
        """AI処理失敗時のフォールバック - 実際の会話から名前抽出"""
        import re
        
        # 実際の会話から名前を抽出
        patient_name = "患者"
        doctor_name = "医師"
        confidence_patient = 0.1
        confidence_doctor = 0.1
        
        # 「田中さん」「山田先生」などのパターンを検索
        patient_patterns = [
            r'([一-龯]{1,4})さん',
            r'患者.*?([一-龯]{1,4})',
            r'([一-龯]{1,4})患者'
        ]
        
        doctor_patterns = [
            r'([一-龯]{1,4})先生',
            r'([一-龯]{1,4})医師',
            r'Dr\.([一-龯]{1,4})'
        ]
        
        # 患者名検索
        for pattern in patient_patterns:
            matches = re.findall(pattern, conversation)
            if matches:
                patient_name = matches[0]
                confidence_patient = 0.7
                break
        
        # 医師名検索
        for pattern in doctor_patterns:
            matches = re.findall(pattern, conversation)
            if matches:
                doctor_name = matches[0]
                confidence_doctor = 0.7
                break
        
        return {
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "confidence_patient": confidence_patient,
            "confidence_doctor": confidence_doctor,
            "reasoning": f"実際の会話から抽出: 患者={patient_name}(信頼度{confidence_patient}), 医師={doctor_name}(信頼度{confidence_doctor})",
            "method": "text_pattern_extraction",
            "process_log": [
                "❌ AI識別失敗",
                "📝 テキストパターン抽出モード",
                "⚠️ Gemini API利用不可", 
                f"✅ 会話解析結果: 患者={patient_name}, 医師={doctor_name}"
            ]
        }

    def convert_to_soap_advanced(self, conversation, patient_name, doctor_name):
        """実際のGemini AIを使用したSOAP変換"""
        
        # AI が利用できない場合のみフォールバック
        if not self.ai_available or not hasattr(self, 'gemini_model'):
            print("⚠️ WARNING: Gemini API利用不可 - SOAP変換フォールバック実行")
            return self._fallback_soap(conversation, patient_name, doctor_name)
        
        # AI分析を強制実行 - 複数回試行
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🤖 Gemini AI SOAP変換実行中... (試行 {attempt + 1}/{max_retries})")
                prompt = f"""
あなたは歯科医療専門のAI分析ツールです。以下の歯科医師と患者の会話をSOAP形式の医療記録に変換してください。

【会話内容】
{conversation}

【患者名】{patient_name}
【医師名】{doctor_name}

以下のJSON形式で回答してください：
{{
    "soap": {{
        "subjective": "患者の主観的訴え・症状（患者が語った症状、痛み、不快感など）",
        "objective": "医師の客観的所見・検査結果（診察で確認した事実、レントゲン結果など）",
        "assessment": "医師の評価・診断（症状の原因、病気の判断、医学的評価）",
        "plan": "治療計画・方針（今後の治療方法、処置内容、次回予定など）"
    }},
    "confidence": 信頼度（0.0-1.0）
}}

SOAP形式の説明：
- S (Subjective): 患者が話した症状や感じていること
- O (Objective): 医師が客観的に観察・検査した事実
- A (Assessment): 医師による診断・評価・判断
- P (Plan): 治療計画や今後の方針

重要な注意事項：
- 各セクションに実際の会話内容から適切な医療情報を分類してください
- 実際の会話内容から逸脱しないでください
- 歯科医療の専門用語を正しく使用してください
- 実際の会話内容から逸脱しないでください

必ずJSON形式で回答してください。説明文は不要です。
"""

                response = self.gemini_model.generate_content(prompt)
                print(f"🔍 DEBUG: SOAP Gemini API Raw Response: '{response.text}'")
                
                # JSONコードブロックを除去してパース
                clean_response = response.text.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]  # ```json を除去
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]  # ``` を除去
                clean_response = clean_response.strip()
                
                print(f"🔍 DEBUG: SOAP Cleaned Response: '{clean_response}'")
                result = json.loads(clean_response)
                
                # 処理ログ追加
                lines_count = len(conversation.split('\n'))
                subjective_length = len(result.get('soap', {}).get('subjective', ''))
                objective_length = len(result.get('soap', {}).get('objective', ''))
                assessment_length = len(result.get('soap', {}).get('assessment', ''))
                plan_length = len(result.get('soap', {}).get('plan', ''))
                
                result["process_log"] = [
                    "🤖 Gemini AI SOAP変換開始",
                    f"📝 解析対象: {lines_count}行の歯科医療会話データ",
                    "🧠 自然言語処理による医療記録構造化実行",
                    f"📊 SOAP分類結果:",
                    f"  - S (主観的情報): {subjective_length}文字",
                    f"  - O (客観的所見): {objective_length}文字",
                    f"  - A (評価・診断): {assessment_length}文字",
                    f"  - P (治療計画): {plan_length}文字",
                    f"✅ Gemini AI SOAP変換完了（信頼度: {result.get('confidence', 0):.2f}）"
                ]
                result["method"] = "gemini_ai_medical_record_structuring"
                
                print(f"✅ Gemini AI SOAP変換完了: 信頼度 {result['confidence']:.2f}")
                return result
                
            except json.JSONDecodeError as e:
                print(f"❌ Gemini AIのJSON応答パースエラー (試行 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    break  # 最後の試行なのでループを抜ける
                continue  # 次の試行
                
            except Exception as e:
                print(f"❌ Gemini AI SOAP変換エラー (試行 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    break  # 最後の試行なのでループを抜ける
                continue  # 次の試行
        
        # 全ての試行が失敗した場合のみフォールバック
        print(f"⚠️ {max_retries}回の試行すべてが失敗 - SOAP変換フォールバック実行")
        return self._fallback_soap(conversation, patient_name, doctor_name)
    
    def _fallback_soap(self, conversation, patient_name, doctor_name):
        """AI処理失敗時のフォールバック - 実際の会話内容から抽出"""
        # 実際の会話内容から基本的なSOAP要素を抽出
        lines = conversation.split('\n')
        patient_lines = [line for line in lines if '患者:' in line or patient_name in line]
        doctor_lines = [line for line in lines if '医師:' in line or doctor_name in line]
        
        # 患者の訴えを抽出
        subjective_content = []
        for line in patient_lines[:3]:  # 最初の3つの発言
            clean_line = line.replace('患者:', '').replace(f'{patient_name}:', '').strip()
            if clean_line and len(clean_line) > 5:
                subjective_content.append(clean_line)
        
        # 医師の所見を抽出
        objective_content = []
        for line in doctor_lines:
            clean_line = line.replace('医師:', '').replace(f'{doctor_name}:', '').strip()
            if '認め' in clean_line or '所見' in clean_line or '検査' in clean_line:
                objective_content.append(clean_line)
        
        # 診断・評価を医師の発言から抽出
        assessment_content = []
        plan_content = []
        for line in doctor_lines:
            clean_line = line.replace('医師:', '').replace(f'{doctor_name}:', '').strip()
            # 診断的発言を抽出
            if any(word in clean_line for word in ['考えられ', '思われ', '診断', '可能性', '症状']):
                assessment_content.append(clean_line)
            # 治療計画を抽出
            if any(word in clean_line for word in ['治療', '処置', '次回', '予約', '経過観察']):
                plan_content.append(clean_line)
        
        # 最後の医師発言を補完用に使用
        if not assessment_content and len(doctor_lines) > 2:
            assessment_content.append(doctor_lines[-2].replace('医師:', '').replace(f'{doctor_name}:', '').strip())
        if not plan_content and doctor_lines:
            plan_content.append(doctor_lines[-1].replace('医師:', '').replace(f'{doctor_name}:', '').strip())
        
        return {
            "soap": {
                "subjective": ' / '.join(subjective_content) if subjective_content else "",
                "objective": ' / '.join(objective_content) if objective_content else "", 
                "assessment": ' / '.join(assessment_content) if assessment_content else "",
                "plan": ' / '.join(plan_content) if plan_content else ""
            },
            "confidence": 0.2,
            "method": "text_extraction_fallback",
            "process_log": [
                "❌ AI SOAP変換失敗",
                "📝 テキスト抽出フォールバックモード",
                "⚠️ Gemini API利用不可",
                f"✅ 実際の会話から抽出: 患者発言{len(patient_lines)}件、医師発言{len(doctor_lines)}件"
            ]
        }

def start_dental_ai_server():
    """歯科AIツール統合サーバーを起動（Gemini AI処理エンジン搭載）"""
    
    # UIディレクトリに移動
    ui_dir = Path(__file__).parent
    os.chdir(ui_dir)
    
    # シンプルポート設定（8001固定）
    PORT = 8001
    print(f"🌐 サーバー起動ポート: {PORT}")
        
    # 最終的な競合チェック（統一システム失敗時のバックアップ）
    if not unified_port_manager_available or PORT == 8001:
        try:
            with socketserver.TCPServer(("", PORT), DentalUIHandler) as test_server:
                pass
        except OSError:
            print(f"❌ ポート {PORT} は既に使用されています")
            print("💡 統一ポート管理システムの利用を推奨します")
            print("📍 確認: /Users/dd/Desktop/1_dev/shared/scripts/unified_port_manager.py")
            return
    
    try:
        with socketserver.TCPServer(("", PORT), DentalUIHandler) as httpd:
            print(f"🌐 歯科AIツール統合サーバー起動中...")
            print(f"📱 UI: http://localhost:{PORT}")
            print(f"🤖 API: http://localhost:{PORT}/api/gemini/health")
            print(f"🛑 停止するには Ctrl+C を押してください")
            
            # ブラウザを自動で開く
            webbrowser.open(f'http://localhost:{PORT}')
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n✅ 統合サーバーを停止しました")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ ポート {PORT} は既に使用されています")
            print(f"💡 別のポートを試すか、既存のプロセスを終了してください")
        else:
            print(f"❌ サーバー起動エラー: {e}")

if __name__ == "__main__":
    start_dental_ai_server()
