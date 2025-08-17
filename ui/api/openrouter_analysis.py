from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime
import openai

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # 環境変数からOpenRouter APIキーを取得
            openrouter_key = os.environ.get('OPENROUTER_API_KEY')
            openrouter_base_url = os.environ.get('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
            
            if not openrouter_key:
                raise Exception("OpenRouter API key not found")
            
            # OpenRouterクライアント初期化（OpenAI SDKを使用、base_urlを変更）
            client = openai.OpenAI(
                api_key=openrouter_key,
                base_url=openrouter_base_url
            )
            
            # POSTデータ取得
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            conversation_text = request_data.get('content', '')
            analysis_type = request_data.get('type', 'quality')
            
            if analysis_type == 'quality':
                result = self.analyze_quality_with_gpt5(client, conversation_text)
            elif analysis_type == 'identification':
                result = self.identify_speakers_with_gpt5(client, conversation_text)
            elif analysis_type == 'soap':
                result = self.convert_to_soap_with_gpt5(client, conversation_text, 
                                                       request_data.get('patient_name', '患者'),
                                                       request_data.get('doctor_name', '医師'))
            else:
                raise Exception(f"Unknown analysis type: {analysis_type}")
            
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "provider": "openrouter"
            }
            
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def analyze_quality_with_gpt5(self, client, conversation_text):
        """GPT-5 via OpenRouterによる最高精度品質分析"""
        
        # GPT-5用の詳細分析プロンプト
        prompt = f"""あなたは歯科医療コミュニケーションの最高位専門分析AIです。GPT-5の高度な推論能力を活用し、以下の歯科診療会話を最高精度で分析してください。

【分析対象の会話】
{conversation_text}

【超高精度分析指示】
以下の観点から0-1の数値で評価し、各評価の詳細な根拠を具体的な発言引用と共に説明してください：

1. **成約可能性** (success_possibility)
   - 患者の治療意欲の強さと継続性
   - 費用・時間コミットメントへの態度
   - 医師への信頼度と専門性認識
   - 治療計画への理解と受容度

2. **患者理解度** (patient_understanding)
   - 医学的説明の理解深度
   - 質問の適切性と専門性
   - 治療リスク・利益の把握度
   - 意思決定に必要な情報の習得状況

3. **治療同意可能性** (treatment_consent_likelihood)
   - 治療への積極的姿勢
   - 懸念・不安の程度と解決可能性
   - 意思決定の準備度
   - 外部要因（家族相談等）の影響

4. **コミュニケーション品質** (communication_quality)
   - 対話の双方向性とバランス
   - 情報伝達の効率性
   - 感情的な信頼関係の構築度
   - 専門用語の適切な使用

5. **医師説明品質** (doctor_explanation)
   - 説明の分かりやすさと適切性
   - 患者の疑問への対応力
   - 医学的正確性と倫理的配慮
   - 患者中心のコミュニケーション実践

【評価基準】（GPT-5高精度判定）
- 0.0-0.2: 非常に低い（重大な問題あり）
- 0.2-0.4: 低い（改善必要）
- 0.4-0.6: 普通（標準的）
- 0.6-0.8: 良い（優良）
- 0.8-1.0: 非常に良い（理想的）

必須出力形式（JSON）：
{{
  "success_possibility": 数値,
  "success_possibility_reasoning": "具体的な発言引用と詳細分析",
  "patient_understanding": 数値,
  "patient_understanding_reasoning": "具体的な発言引用と詳細分析",
  "treatment_consent_likelihood": 数値,
  "treatment_consent_reasoning": "具体的な発言引用と詳細分析",
  "communication_quality": 数値,
  "communication_quality_reasoning": "対話品質の詳細分析",
  "doctor_explanation": 数値,
  "doctor_explanation_reasoning": "医師説明の詳細分析",
  "improvement_suggestions": ["具体的改善提案1", "具体的改善提案2", "具体的改善提案3"],
  "positive_aspects": ["良い点1", "良い点2", "良い点3"],
  "confidence": 数値,
  "method": "gpt-5_openrouter_analysis"
}}"""

        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "あなたはGPT-5の能力を最大限活用する歯科医療コミュニケーション最高位専門分析AIです。極めて正確で詳細な分析を行い、必ずJSONフォーマットで結果を返してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # 一貫性重視
            max_tokens=3000
        )
        
        result_text = response.choices[0].message.content
        
        # JSONの抽出と解析
        try:
            # JSONブロックの抽出（```json...```形式対応）
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                json_content = result_text[json_start:json_end].strip()
            elif "{" in result_text and "}" in result_text:
                json_start = result_text.find("{")
                json_end = result_text.rfind("}") + 1
                json_content = result_text[json_start:json_end]
            else:
                raise ValueError("JSONが見つかりません")
                
            result = json.loads(json_content)
            
        except (json.JSONDecodeError, ValueError) as e:
            # JSONパースエラーの場合、デフォルト構造で応答
            result = {
                "success_possibility": 0.5,
                "success_possibility_reasoning": "GPT-5応答のJSONパースエラーのためデフォルト値を使用",
                "patient_understanding": 0.5,
                "patient_understanding_reasoning": "GPT-5応答のJSONパースエラーのためデフォルト値を使用",
                "treatment_consent_likelihood": 0.5,
                "treatment_consent_reasoning": "GPT-5応答のJSONパースエラーのためデフォルト値を使用",
                "communication_quality": 0.5,
                "communication_quality_reasoning": "GPT-5応答のJSONパースエラーのためデフォルト値を使用",
                "doctor_explanation": 0.5,
                "doctor_explanation_reasoning": "GPT-5応答のJSONパースエラーのためデフォルト値を使用",
                "improvement_suggestions": ["GPT-5応答解析エラーのため詳細分析不可"],
                "positive_aspects": ["GPT-5応答解析エラーのため詳細分析不可"],
                "confidence": 0.3,
                "method": "gpt-5_openrouter_fallback",
                "parse_error": str(e),
                "raw_response": result_text[:500]
            }
        
        result["timestamp"] = datetime.utcnow().isoformat() + "Z"
        result["provider"] = "openrouter"
        result["model"] = "gpt-5"
        
        return result
    
    def identify_speakers_with_gpt5(self, client, conversation_text):
        """GPT-5による超高精度話者識別"""
        
        prompt = f"""あなたはGPT-5の高度言語理解能力を活用する話者識別専門AIです。以下の歯科診療会話から患者と医師を最高精度で特定してください。

【会話内容】
{conversation_text}

【超高精度特定指示】
1. 実名抽出：「○○さん」「○○先生」「Dr.○○」等から正確な名前を抽出
2. 役割推定：発言内容、専門用語使用、質問パターンから役割を判定
3. 信頼度評価：特定根拠の強さを0-1で数値化
4. 根拠説明：具体的な発言を引用し、判定理由を詳述

出力形式（JSON）：
{{
  "patient_name": "患者名",
  "doctor_name": "医師名",
  "confidence_patient": 数値,
  "confidence_doctor": 数値,
  "reasoning": "詳細な特定根拠と発言引用",
  "method": "gpt-5_openrouter_identification"
}}"""

        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "あなたはGPT-5の能力を最大活用する話者識別専門AIです。正確な分析をJSONで返してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        result_text = response.choices[0].message.content
        
        try:
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                json_content = result_text[json_start:json_end].strip()
            else:
                json_start = result_text.find("{")
                json_end = result_text.rfind("}") + 1
                json_content = result_text[json_start:json_end]
                
            result = json.loads(json_content)
            
        except (json.JSONDecodeError, ValueError):
            result = {
                "patient_name": "患者",
                "doctor_name": "医師",
                "confidence_patient": 0.5,
                "confidence_doctor": 0.5,
                "reasoning": "GPT-5応答解析エラーのためデフォルト値を使用",
                "method": "gpt-5_openrouter_fallback"
            }
        
        result["provider"] = "openrouter"
        result["model"] = "gpt-5"
        return result
    
    def convert_to_soap_with_gpt5(self, client, conversation_text, patient_name, doctor_name):
        """GPT-5による最高精度SOAP形式変換"""
        
        prompt = f"""あなたはGPT-5の医療知識とテキスト理解能力を最大活用する歯科SOAP記録専門AIです。以下の診療会話を最高精度でSOAP形式に変換してください。

【会話内容】
{conversation_text}

【患者名】{patient_name}
【医師名】{doctor_name}

【GPT-5高精度SOAP変換指示】

**S (Subjective - 主観的情報)**
- 患者の主訴と症状詳細
- 既往歴・現病歴・服薬・アレルギー情報
- 患者の懸念・要望

**O (Objective - 客観的所見)**
- 口腔内診察所見（歯式表記：FDI方式）
- 歯周検査結果（PPD、BOP、動揺度）
- 画像診断所見
- 口腔外診察・バイタルサイン

**A (Assessment - 評価・診断)**
- 歯科診断名（ICD-10準拠）
- 病態評価・重症度・予後判定
- リスク評価

**P (Plan - 治療計画)**
- 実施処置内容
- 今後の治療計画
- 次回予約・継続治療
- 患者指導・処方薬

出力形式（JSON）：
{{
  "S": "主観的情報の詳細記録",
  "O": "客観的所見の詳細記録",
  "A": "評価・診断の詳細記録", 
  "P": "治療計画の詳細記録",
  "confidence": 数値,
  "dental_specifics": {{
    "affected_teeth": ["影響を受けた歯番号"],
    "procedures_performed": ["実施された処置"],
    "follow_up_needed": true/false
  }},
  "incomplete_info": ["不足している情報"],
  "method": "gpt-5_openrouter_soap"
}}"""

        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "あなたはGPT-5の能力を最大活用する歯科SOAP記録専門AIです。正確で詳細な医療記録をJSONで作成してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2500
        )
        
        result_text = response.choices[0].message.content
        
        try:
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                json_content = result_text[json_start:json_end].strip()
            else:
                json_start = result_text.find("{")
                json_end = result_text.rfind("}") + 1
                json_content = result_text[json_start:json_end]
                
            result = json.loads(json_content)
            
        except (json.JSONDecodeError, ValueError):
            result = {
                "S": "GPT-5応答解析エラーのため詳細分析不可",
                "O": "GPT-5応答解析エラーのため詳細分析不可",
                "A": "GPT-5応答解析エラーのため詳細分析不可",
                "P": "GPT-5応答解析エラーのため詳細分析不可",
                "confidence": 0.3,
                "dental_specifics": {
                    "affected_teeth": [],
                    "procedures_performed": [],
                    "follow_up_needed": False
                },
                "incomplete_info": ["GPT-5応答解析エラーのため詳細分析不可"],
                "method": "gpt-5_openrouter_fallback"
            }
        
        result["provider"] = "openrouter"
        result["model"] = "gpt-5"
        return result
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()