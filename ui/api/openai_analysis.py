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
            
            # 環境変数からAPIキーを取得
            openai_key = os.environ.get('OPENAI_API_KEY')
            if not openai_key:
                raise Exception("OpenAI API key not found")
            
            # OpenAIクライアント初期化
            client = openai.OpenAI(api_key=openai_key)
            
            # POSTデータ取得
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            conversation_text = request_data.get('content', '')
            analysis_type = request_data.get('type', 'quality')
            
            if analysis_type == 'quality':
                result = self.analyze_quality_with_gpt41(client, conversation_text)
            elif analysis_type == 'identification':
                result = self.identify_speakers_with_gpt41(client, conversation_text)
            elif analysis_type == 'soap':
                result = self.convert_to_soap_with_gpt41(client, conversation_text, 
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
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def analyze_quality_with_gpt41(self, client, conversation_text):
        """GPT-4.1による高精度品質分析"""
        
        # Structured Output用のJSONスキーマ定義
        quality_schema = {
            "type": "object",
            "properties": {
                "success_possibility": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "成約可能性 (0-1)"
                },
                "success_possibility_reasoning": {
                    "type": "string",
                    "description": "成約可能性の詳細な根拠説明"
                },
                "patient_understanding": {
                    "type": "number", 
                    "minimum": 0,
                    "maximum": 1,
                    "description": "患者理解度 (0-1)"
                },
                "patient_understanding_reasoning": {
                    "type": "string",
                    "description": "患者理解度の詳細な根拠説明"
                },
                "treatment_consent_likelihood": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "治療同意可能性 (0-1)"
                },
                "treatment_consent_reasoning": {
                    "type": "string",
                    "description": "治療同意可能性の詳細な根拠説明"
                },
                "improvement_suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "改善提案リスト"
                },
                "positive_aspects": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "良い点のリスト"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "分析の信頼度"
                }
            },
            "required": [
                "success_possibility", "success_possibility_reasoning",
                "patient_understanding", "patient_understanding_reasoning", 
                "treatment_consent_likelihood", "treatment_consent_reasoning",
                "improvement_suggestions", "positive_aspects", "confidence"
            ],
            "additionalProperties": False
        }
        
        prompt = f"""あなたは歯科医療コミュニケーションの専門分析AIです。以下の歯科診療会話を詳細に分析し、医療ビジネスの観点から評価してください。

【分析対象の会話】
{conversation_text}

【分析指示】
以下の3つの観点から0-1の数値で評価し、各評価の詳細な根拠を説明してください：

1. **成約可能性** (success_possibility)
   - 患者が治療を受ける意向の強さ
   - 費用や時間への前向きな反応
   - 医師への信頼度
   - 具体的な治療計画への関心

2. **患者理解度** (patient_understanding) 
   - 医師の説明に対する理解の深さ
   - 質問の質と内容
   - 専門用語への反応
   - 治療方法の把握度

3. **治療同意可能性** (treatment_consent_likelihood)
   - 治療への積極性
   - 不安や迷いの程度
   - 決断への準備度
   - 家族相談の必要性

【評価基準】
- 0.0-0.3: 低い（問題あり、改善必要）
- 0.3-0.6: 普通（標準的）
- 0.6-0.8: 良い（優良）
- 0.8-1.0: 非常に良い（理想的）

各評価の根拠説明では、会話中の具体的な発言を引用し、なぜその評価になったかを詳しく説明してください。

改善提案と良い点も具体的に挙げてください。"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは歯科医療コミュニケーションの専門分析AIです。正確で詳細な分析を行い、構造化されたJSONで結果を返してください。"},
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "quality_analysis",
                    "schema": quality_schema
                }
            },
            temperature=0.1,  # 一貫性を重視
            max_tokens=2000
        )
        
        result = json.loads(response.choices[0].message.content)
        result["method"] = "gpt-4.1_structured_analysis"
        result["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        return result
    
    def identify_speakers_with_gpt41(self, client, conversation_text):
        """GPT-4.1による高精度話者識別"""
        
        identification_schema = {
            "type": "object",
            "properties": {
                "patient_name": {"type": "string"},
                "doctor_name": {"type": "string"},
                "confidence_patient": {"type": "number", "minimum": 0, "maximum": 1},
                "confidence_doctor": {"type": "number", "minimum": 0, "maximum": 1},
                "reasoning": {"type": "string"},
                "method": {"type": "string"}
            },
            "required": ["patient_name", "doctor_name", "confidence_patient", "confidence_doctor", "reasoning", "method"]
        }
        
        prompt = f"""以下の歯科診療会話から患者と医師の名前を正確に特定してください。

【会話内容】
{conversation_text}

【特定指示】
1. 患者の名前：「○○さん」「患者の○○」等から実名を抽出
2. 医師の名前：「○○先生」「Dr.○○」「医師の○○」等から実名を抽出
3. 名前が明記されていない場合は話者パターンから推定
4. 各特定結果の信頼度を0-1で評価
5. 特定根拠を詳しく説明

事実に基づいて正確に特定してください。"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは医療会話分析の専門AIです。話者を正確に特定し、構造化されたJSONで結果を返してください。"},
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_schema", 
                "json_schema": {
                    "name": "speaker_identification",
                    "schema": identification_schema
                }
            },
            temperature=0.1
        )
        
        return json.loads(response.choices[0].message.content)
    
    def convert_to_soap_with_gpt41(self, client, conversation_text, patient_name, doctor_name):
        """GPT-4.1による高精度SOAP形式変換"""
        
        soap_schema = {
            "type": "object",
            "properties": {
                "S": {"type": "string", "description": "主観的情報"},
                "O": {"type": "string", "description": "客観的所見"},
                "A": {"type": "string", "description": "評価・診断"},
                "P": {"type": "string", "description": "治療計画"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "dental_specifics": {
                    "type": "object",
                    "properties": {
                        "affected_teeth": {"type": "array", "items": {"type": "string"}},
                        "procedures_performed": {"type": "array", "items": {"type": "string"}},
                        "follow_up_needed": {"type": "boolean"}
                    }
                },
                "incomplete_info": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["S", "O", "A", "P", "confidence", "dental_specifics", "incomplete_info"]
        }
        
        prompt = f"""あなたは歯科医療記録の専門家です。以下の歯科診療会話をSOAP形式の診療記録に変換してください。

【会話内容】
{conversation_text}

【患者名】{patient_name}
【医師名】{doctor_name}

【歯科SOAP記録の変換指示】

**S (Subjective - 主観的情報)**
- 患者の主訴（chief complaint）
- 症状の詳細（痛みの程度・性質、いつから等）
- 既往歴・現病歴
- 服薬状況、アレルギー情報

**O (Objective - 客観的所見)**
- 口腔内診察所見（歯式表記使用：例「#17 C4」「46番 Per」）
- 歯周検査結果（PPD、BOP、動揺度等の数値）
- レントゲン・画像診断所見
- 口腔外診察所見（リンパ節、顎関節等）
- バイタルサイン（必要時）

**A (Assessment - 評価・診断)**
- 歯科診断名（ICD-10対応）
- 病態評価・重症度判定
- 予後判断
- リスク評価

**P (Plan - 治療計画)**
- 今回実施した処置内容
- 今後の治療計画（段階的計画含む）
- 次回予約・継続治療予定
- 患者指導内容（口腔ケア指導、生活指導等）
- 処方薬（薬剤名、用法用量）

【歯科記録特有の注意事項】
- 歯式表記：FDI方式（11-48）または日本式（1番-8番）を使用
- 歯面表記：M（近心）、D（遠心）、B（頬側）、L（舌側）、O（咬合面）
- 歯周状態：PPD（mm）、BOP（±）、動揺度（0-3度）で記録
- 処置内容：保険点数コードも併記（可能な場合）
- 不確実な診断には「疑い」を付記

【品質管理】
- 医療用語の正確性を最優先
- 推測や解釈は避け、記録された事実のみを使用
- 部位不明な場合は「部位不明」と明記
- 数値データは正確に転記"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは歯科医療記録の専門家です。正確で詳細なSOAP記録を作成し、構造化されたJSONで結果を返してください。"},
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "soap_conversion", 
                    "schema": soap_schema
                }
            },
            temperature=0.1,
            max_tokens=2000
        )
        
        return json.loads(response.choices[0].message.content)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()