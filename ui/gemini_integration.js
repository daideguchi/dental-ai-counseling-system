/**
* Gemini API統合用JavaScript - 改善版
* 旧ファイルに混入していた \n などのリテラルが原因で SyntaxError になっていたため、改行を正規化
*/

class GeminiIntegration {
 constructor() {
   this.apiEndpoint = '/api/gemini'; // 実際のAPIエンドポイント
   this.isConnected = false;
   this.rateLimitDelay = 1000; // レート制限対応
 }

 // APIの接続確認
 async checkConnection() {
   try {
     const response = await fetch(`${this.apiEndpoint}/health`, {
       method: 'GET'
     });
     this.isConnected = response.ok;
     return this.isConnected;
   } catch (error) {
     console.warn('Gemini API接続確認失敗:', error.message);
     this.isConnected = false;
     return false;
   }
 }

 // 患者・医師自動特定（改善版）
 async identifyPatientDoctor(conversationText) {
   if (!this.isConnected) {
     return this.fallbackIdentification(conversationText);
   }

   try {
     const response = await fetch(`${this.apiEndpoint}/identify`, {
       method: 'POST',
       headers: {
         'Content-Type': 'application/json',
         'X-API-Version': '2024-01'
       },
       body: JSON.stringify({
         conversation: conversationText,
         context: 'dental_consultation',
         language: 'ja'
       })
     });

     if (!response.ok) {
       throw new Error(`HTTP ${response.status}: ${response.statusText}`);
     }

     const result = await response.json();
     return this.validateIdentificationResult(result);
   } catch (error) {
     console.error('患者・医師特定エラー:', error);
     return this.fallbackIdentification(conversationText);
   }
 }

 // フォールバック特定処理
 fallbackIdentification(conversationText) {
   let patientName = '患者';
   let doctorName = '医師';
   let confidence = 0.5;

   // 基本的なパターンマッチング
   const patientPatterns = [
     /([一-龯]{2,4})さん/g,
     /患者.*?([一-龯]{2,4})/g
   ];

   const doctorPatterns = [
     /([一-龯]{2,4})先生/g,
     /Dr\.?\s*([一-龯]{2,4})/g,
     /医師.*?([一-龯]{2,4})/g
   ];

   // 患者名検索
   patientPatterns.forEach(pattern => {
     const matches = conversationText.match(pattern);
     if (matches && matches.length > 0) {
       patientName = matches[0].replace(/さん|患者/g, '').trim();
       confidence = Math.max(confidence, 0.7);
     }
   });

   // 医師名検索
   doctorPatterns.forEach(pattern => {
     const matches = conversationText.match(pattern);
     if (matches && matches.length > 0) {
       doctorName = matches[0].replace(/先生|医師|Dr\.?/g, '').trim();
       confidence = Math.max(confidence, 0.7);
     }
   });

   return {
     patient_name: patientName,
     doctor_name: doctorName,
     confidence_patient: confidence,
     confidence_doctor: confidence,
     reasoning: 'フォールバック処理による推定',
     method: 'pattern_matching'
   };
 }

 // SOAP形式変換（改善版）
 async convertToSOAP(conversationText, patientName = '患者', doctorName = '医師') {
   if (!this.isConnected) {
     return this.fallbackSOAPConversion(conversationText);
   }

   try {
     const response = await fetch(`${this.apiEndpoint}/soap`, {
       method: 'POST',
       headers: {
         'Content-Type': 'application/json',
         'X-API-Version': '2024-01'
       },
       body: JSON.stringify({
         conversation: conversationText,
         patient_name: patientName,
         doctor_name: doctorName,
         specialty: 'dentistry',
         language: 'ja',
         format_version: 'soap_v2'
       })
     });

     if (!response.ok) {
       throw new Error(`HTTP ${response.status}: ${response.statusText}`);
     }

     const result = await response.json();
     return this.validateSOAPResult(result);
   } catch (error) {
     console.error('SOAP変換エラー:', error);
     return this.fallbackSOAPConversion(conversationText);
   }
 }

 // フォールバックSOAP変換
 fallbackSOAPConversion(conversationText) {
   // 高度なキーワード分析
   const dentalKeywords = {
     subjective: {
       pain: ['痛い', '痛み', 'ズキズキ', 'キーン', '激痛', '鈍痛'],
       sensitivity: ['しみる', 'ピリピリ', '冷たい', '熱い'],
       discomfort: ['違和感', '不快', '気持ち悪い', 'むずむず'],
       swelling: ['腫れ', '腫れた', '膨らんだ'],
       bleeding: ['血が出る', '出血', '血'],
       others: ['気になる', '心配', '不安']
     },
     objective: {
       caries: ['う蝕', '虫歯', 'カリエス', 'C1', 'C2', 'C3', 'C4'],
       periodontal: ['歯肉炎', '歯周病', '歯石', 'プラーク', 'BOP'],
       examination: ['打診痛', '冷水痛', '温熱痛', '咬合痛', '圧痛'],
       findings: ['腫脹', '発赤', '排膿', '動揺', '変色'],
       xray: ['X線', 'レントゲン', 'CT', '透過像', '不透過像']
     },
     assessment: {
       diagnosis: ['診断', '疑い', '可能性', '病名'],
       conditions: ['急性', '慢性', '軽度', '中等度', '重度'],
       prognosis: ['予後', '経過', '治癒', '改善']
     },
     plan: {
       treatment: ['治療', '処置', '手術', '抜歯', '充填'],
       materials: ['CR', 'インレー', 'クラウン', 'ブリッジ', 'インプラント'],
       procedures: ['根管治療', 'スケーリング', 'SRP', '麻酔'],
       followup: ['経過観察', '定期検診', '再評価', '次回']
     }
   };

   const soap = { S: '', O: '', A: '', P: '' };
   const lines = conversationText.split('\n').filter(line => line.trim());

   // 発言者別に分類
   const patientLines = [];
   const doctorLines = [];

   lines.forEach(line => {
     if (line.includes('患者') || line.includes('Speaker B') || line.includes('発言者B')) {
       patientLines.push(line);
     } else if (line.includes('医師') || line.includes('Speaker A') || line.includes('発言者A') || line.includes('先生')) {
       doctorLines.push(line);
     }
   });

   // S: 主観的情報の抽出
   const subjectiveStatements = [];
   patientLines.forEach(line => {
     Object.values(dentalKeywords.subjective).flat().forEach(keyword => {
       if (line.includes(keyword)) {
         subjectiveStatements.push(line.replace(/^.*?:/, '').trim());
       }
     });
   });

   soap.S = subjectiveStatements.length > 0 ?
     subjectiveStatements.slice(0, 3).join('。 ') :
     '特記すべき主観的症状は認められない。';

   // O: 客観的所見の抽出
   const objectiveStatements = [];
   doctorLines.forEach(line => {
     Object.values(dentalKeywords.objective).flat().forEach(keyword => {
       if (line.includes(keyword)) {
         objectiveStatements.push(line.replace(/^.*?:/, '').trim());
       }
     });
   });

   soap.O = objectiveStatements.length > 0 ?
     objectiveStatements.slice(0, 3).join('。 ') :
     '口腔内診査を実施。特記すべき異常所見なし。';

   // A: 評価・診断の抽出
   const assessmentStatements = [];
   doctorLines.forEach(line => {
     Object.values(dentalKeywords.assessment).flat().forEach(keyword => {
       if (line.includes(keyword)) {
         assessmentStatements.push(line.replace(/^.*?:/, '').trim());
       }
     });
   });

   soap.A = assessmentStatements.length > 0 ?
     assessmentStatements.slice(0, 2).join('。 ') :
     '詳細な診断のため追加検査が必要。';

   // P: 治療計画の抽出
   const planStatements = [];
   doctorLines.forEach(line => {
     Object.values(dentalKeywords.plan).flat().forEach(keyword => {
       if (line.includes(keyword)) {
         planStatements.push(line.replace(/^.*?:/, '').trim());
       }
     });
   });

   soap.P = planStatements.length > 0 ?
     planStatements.slice(0, 3).join('。 ') :
     '治療計画を検討し、患者と相談の上決定する。';

   return {
     ...soap,
     confidence: 0.75,
     key_points: [
       `患者発言: ${patientLines.length}件`,
       `医師発言: ${doctorLines.length}件`,
       `抽出キーワード: ${subjectiveStatements.length + objectiveStatements.length + assessmentStatements.length + planStatements.length}件`
     ],
     method: 'keyword_analysis'
   };
 }

 // 会話品質分析（改善版）
 async analyzeQuality(conversationText) {
   if (!this.isConnected) {
     return this.fallbackQualityAnalysis(conversationText);
   }

   try {
     const response = await fetch(`${this.apiEndpoint}/quality`, {
       method: 'POST',
       headers: {
         'Content-Type': 'application/json',
         'X-API-Version': '2024-01'
       },
       body: JSON.stringify({
         conversation: conversationText,
         analysis_type: 'comprehensive',
         specialty: 'dentistry',
         language: 'ja'
       })
     });

     if (!response.ok) {
       throw new Error(`HTTP ${response.status}: ${response.statusText}`);
     }

     const result = await response.json();
     return this.validateQualityResult(result);
   } catch (error) {
     console.error('品質分析エラー:', error);
     return this.fallbackQualityAnalysis(conversationText);
   }
 }

 // フォールバック品質分析
 fallbackQualityAnalysis(conversationText) {
   const analysis = {
     communication_quality: 0.5,
     patient_understanding: 0.5,
     doctor_explanation: 0.5,
     treatment_consent_likelihood: 0.5,
     improvement_suggestions: [],
     positive_aspects: []
   };

   const lines = conversationText.split('\n').filter(line => line.trim());
   const totalLines = lines.length;

   // コミュニケーション品質の評価
   const questionCount = (conversationText.match(/\?|ですか|でしょうか|いかがですか/g) || []).length;
   const explanationCount = (conversationText.match(/説明|ご説明|お話し|について/g) || []).length;

   analysis.communication_quality = Math.min(0.95,
     (questionCount * 0.1 + explanationCount * 0.05 + totalLines * 0.02));

   // 患者理解度の評価
   const understandingWords = ['分かりました', 'はい', 'そうですね', '理解', 'なるほど'];
   const confusionWords = ['分からない', 'よく分からない', '難しい', '？'];

   let understandingScore = 0.5;
   understandingWords.forEach(word => {
     if (conversationText.includes(word)) understandingScore += 0.1;
   });
   confusionWords.forEach(word => {
     if (conversationText.includes(word)) understandingScore -= 0.1;
   });

   analysis.patient_understanding = Math.max(0.1, Math.min(0.95, understandingScore));

   // 医師の説明品質
   const technicalTerms = ['う蝕', '歯髄', '根管', '歯周', 'プラーク'];
   const easyExplanations = ['簡単に言うと', 'つまり', '例えば', 'わかりやすく'];

   let explanationScore = 0.5;
   technicalTerms.forEach(term => {
     if (conversationText.includes(term)) explanationScore += 0.05;
   });
   easyExplanations.forEach(phrase => {
     if (conversationText.includes(phrase)) explanationScore += 0.1;
   });

   analysis.doctor_explanation = Math.min(0.95, explanationScore);

   // 治療同意可能性
   const consentWords = ['お願いします', 'やります', '受けます', '同意'];
   const hesitationWords = ['考えさせて', '迷って', '不安', '心配'];

   let consentScore = 0.7;
   consentWords.forEach(word => {
     if (conversationText.includes(word)) consentScore += 0.1;
   });
   hesitationWords.forEach(word => {
     if (conversationText.includes(word)) consentScore -= 0.1;
   });

   analysis.treatment_consent_likelihood = Math.max(0.1, Math.min(0.95, consentScore));

   // 改善提案の生成
   if (analysis.communication_quality < 0.7) {
     analysis.improvement_suggestions.push('より多くの質問で患者の状況を確認する');
   }
   if (analysis.patient_understanding < 0.7) {
     analysis.improvement_suggestions.push('専門用語の説明をより丁寧に行う');
   }
   if (analysis.doctor_explanation < 0.7) {
     analysis.improvement_suggestions.push('視覚的な資料を使用して説明する');
   }
   if (!conversationText.includes('費用') && !conversationText.includes('料金')) {
     analysis.improvement_suggestions.push('治療費用について説明する');
   }
   if (!conversationText.includes('期間') && !conversationText.includes('回数')) {
     analysis.improvement_suggestions.push('治療期間・回数について説明する');
   }

   // 良い点の抽出
   if (analysis.communication_quality >= 0.8) {
     analysis.positive_aspects.push('十分なコミュニケーションが取れている');
   }
   if (conversationText.includes('ありがとう')) {
     analysis.positive_aspects.push('良好な医師・患者関係');
   }
   if (explanationCount >= 3) {
     analysis.positive_aspects.push('詳細な説明を実施');
   }
   if (questionCount >= 2) {
     analysis.positive_aspects.push('適切な問診を実施');
   }

   // デフォルト値の設定
   if (analysis.improvement_suggestions.length === 0) {
     analysis.improvement_suggestions.push('現在の対応は適切です');
   }
   if (analysis.positive_aspects.length === 0) {
     analysis.positive_aspects.push('基本的な診療が実施されています');
   }

   return analysis;
 }

 // 結果の検証
 validateIdentificationResult(result) {
   const required = ['patient_name', 'doctor_name', 'confidence_patient', 'confidence_doctor'];
   for (const field of required) {
     if (!Object.prototype.hasOwnProperty.call(result, field)) {
       throw new Error(`Missing required field: ${field}`);
     }
   }

   // 信頼度の範囲チェック
   result.confidence_patient = Math.max(0, Math.min(1, result.confidence_patient));
   result.confidence_doctor = Math.max(0, Math.min(1, result.confidence_doctor));

   return result;
 }

 validateSOAPResult(result) {
   const required = ['S', 'O', 'A', 'P'];
   for (const field of required) {
     if (!Object.prototype.hasOwnProperty.call(result, field)) {
       result[field] = `${field}情報が不足しています`;
     }
   }

   if (!result.confidence) result.confidence = 0.5;
   if (!result.key_points) result.key_points = [];

   return result;
 }

 validateQualityResult(result) {
   const defaultValues = {
     communication_quality: 0.5,
     patient_understanding: 0.5,
     doctor_explanation: 0.5,
     treatment_consent_likelihood: 0.5,
     improvement_suggestions: ['分析結果が不完全です'],
     positive_aspects: ['基本的な診療を実施']
   };

   for (const [key, defaultValue] of Object.entries(defaultValues)) {
     if (!Object.prototype.hasOwnProperty.call(result, key)) {
       result[key] = defaultValue;
     }
   }

   return result;
 }

 // デモ用のローカル処理（API接続なしでも動作）
 async processLocalDemo(conversationText) {
   console.log('🎭 デモモード: ローカル処理を実行');

   // 実際の内容を解析
   const identification = this.fallbackIdentification(conversationText);
   const soap = this.fallbackSOAPConversion(conversationText);
   const quality = this.fallbackQualityAnalysis(conversationText);

   // 処理時間のシミュレート
   await new Promise(resolve => setTimeout(resolve, 2000));

   return {
     identification,
     soap,
     quality,
     metadata: {
       processing_time: '2.5s',
       method: 'local_fallback',
       api_connected: false,
       timestamp: new Date().toISOString()
     }
   };
 }

 // レート制限対応の遅延処理
 async rateLimitedRequest(requestFn) {
   await new Promise(resolve => setTimeout(resolve, this.rateLimitDelay));
   return await requestFn();
 }

 // エラーハンドリング強化
 handleAPIError(error, context) {
   const errorInfo = {
     context,
     error: error.message,
     timestamp: new Date().toISOString(),
     userAgent: navigator.userAgent
   };

   console.error('Gemini API Error:', errorInfo);

   // エラー報告（実装時にAPIエンドポイントに送信）
   if (typeof window !== 'undefined') {
     window.dispatchEvent(new CustomEvent('gemini-error', { detail: errorInfo }));
   }
 }
}

// シングルトンインスタンス
const geminiIntegration = new GeminiIntegration();

// 初期化時にAPI接続確認
document.addEventListener('DOMContentLoaded', async () => {
 console.log('🔌 Gemini API接続確認中...');
 const connected = await geminiIntegration.checkConnection();
 console.log(connected ? '✅ Gemini API接続成功' : '⚠️ Gemini APIオフライン（フォールバック使用）');
});

// グローバルに公開
if (typeof window !== 'undefined') {
 window.geminiIntegration = geminiIntegration;

 // デバッグ用
 window.debugGemini = {
   testIdentification: (text) => geminiIntegration.fallbackIdentification(text),
   testSOAP: (text) => geminiIntegration.fallbackSOAPConversion(text),
   testQuality: (text) => geminiIntegration.fallbackQualityAnalysis(text)
 };
}

console.log('🧠 Gemini統合システム初期化完了');